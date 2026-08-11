"""3주차 D3 — RAG · 내 문서로 답하게 하기"""
from nbkit import md, code, h, lab, prep, Ex, Task

BASE = 'https://tunalee.github.io/posco/data/docs/'

CELLS = [
    md("## 1. 준비"),
    md("오늘 만드는 것은 **문서를 찾아 읽고 그 근거로만 답하는 비서**다.\n\n"
       "「연차는 며칠까지 쓸 수 있어?」 라고 물으면 법 조문을 찾아 그 안에서 답한다.\n"
       "모델이 아는 것으로 답하지 않는다. **찾은 문장에 없으면 없다고 답한다.**"),
    md("문서는 **실제 법령 조문**을 쓴다. 지어낸 글이 아니라서 답이 맞았는지 원문과 대조할 수 있다.\n\n"
       "| 파일 | 무엇 | 왜 이걸 쓰나 |\n|---|---|---|\n"
       "| `labor_standards.txt` | 근로기준법 | 연차 · 근로시간 — 누구나 물어보는 것 |\n"
       "| `occupational_safety.txt` | 산업안전보건법 | 안전보건교육 · 작업중지 — 현장 질문 |\n"
       "| `industrial_tech.txt` | 산업기술보호법 | 국가핵심기술 — 어제 반출 이야기와 이어진다 |\n"
       "| `privacy.txt` | 개인정보 보호법 | 수집 · 이용 · 파기 |\n\n"
       "> 법령은 저작권법 제7조에 따라 보호 대상이 아니라 그대로 쓸 수 있다. 출처는 위키문헌이다."),

    prep("""# 문서 네 개를 받아 온다. 사내에서는 이 자리가 공유 폴더나 문서함이 된다.
import urllib.request, re, json

BASE = '%s'
FILES = {'근로기준법': 'labor_standards.txt', '산업안전보건법': 'occupational_safety.txt',
         '산업기술보호법': 'industrial_tech.txt', '개인정보보호법': 'privacy.txt'}

DOCS = {}
for name, fn in FILES.items():
    raw = urllib.request.urlopen(BASE + fn, timeout=60).read().decode('utf-8')
    DOCS[name] = '\\n'.join(l for l in raw.split('\\n') if not l.startswith('#'))   # 머리말 주석은 뺀다
    print('%%-12s %%6d자' %% (name, len(DOCS[name])))""" % BASE),

    md("네 파일에 **14만 자**가 있다. 이걸 통째로 모델에 넣을 수는 없다.\n"
       "넣을 수 있다 해도, 답과 상관없는 13만 자가 같이 들어가면 **정확도가 떨어진다**."),

    md("## 2. 자르기"),
    md("문서를 찾을 수 있는 크기로 자른다. 법령은 **조문 단위**가 자연스럽다.\n"
       "「제60조(연차 유급휴가) …」 한 덩어리가 질문 하나에 대응하기 때문이다."),

    prep("""# 조문 번호 앞에서 자른다. 사내 문서라면 「제N조」 대신 제목·번호 규칙을 쓴다.
def split_articles(text, source):
    parts = re.split(r'\\n(?=제\\d+조)', text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p) < 40:                       # 너무 짧은 조각은 버린다
            continue
        title = p.split('\\n')[0][:40]
        out.append({'source': source, 'title': title, 'text': p})
    return out

CHUNKS = []
for name, text in DOCS.items():
    CHUNKS += split_articles(text, name)
print('조각 %d개' % len(CHUNKS))
print('평균 %d자 · 가장 긴 것 %d자' % (sum(len(c['text']) for c in CHUNKS) / len(CHUNKS),
                                max(len(c['text']) for c in CHUNKS)))"""),

    code("""# 실제로 어떻게 잘렸는지 세 개만 본다
for c in CHUNKS[:3]:
    print('[%s] %s' % (c['source'], c['title']))
    print('   ', c['text'][:70].replace('\\n', ' '), '...')
    print()"""),

    md("조각 하나가 **조문 하나**다. 제목이 붙어 있어서 나중에 출처를 댈 수 있다.\n"
       "글자 수로 잘랐다면 「제60조」의 앞뒤가 다른 조각으로 흩어졌을 것이다."),

    Ex(1, "글자 수로 자르면 어떻게 달라지는지 본다. **300** 을 넣어 조각 수를 견준다.\n"
          "> 조문으로 자른 것과 몇 배 차이가 나는지, 조각 하나가 말이 되는지 본다.",
       setup="# 같은 문서를 기계적으로 N글자마다 자른다",
       blank="SIZE = ___",
       answer="SIZE = 300",
       check="""t = DOCS['근로기준법']
rough = [t[i:i+SIZE] for i in range(0, len(t), SIZE)]
print('%d자로 자르면 %d조각 · 조문으로 자르면 %d조각'
      % (SIZE, len(rough), len([c for c in CHUNKS if c['source'] == '근로기준법'])))
print()
print('세 번째 조각:', rough[2][:80].replace('\\n', ' '))"""),

    md("기계적으로 자르면 **문장 한가운데서 끊긴다**. 그 조각만 읽어서는 무슨 말인지 모른다.\n"
       "검색이 그 조각을 가져와도 답이 안 나온다. **자르는 자리가 검색 품질을 정한다.**"),

    md("## 3. 찾기"),
    md("이제 질문에 맞는 조각을 찾는다. 먼저 **낱말이 겹치는 정도**로 찾아 본다.\n"
       "가장 단순한 방법이고, 어디서 막히는지 보고 나면 임베딩이 왜 필요한지 알게 된다."),

    prep("""# 낱말이 겹치는 정도로 순위를 매긴다 (TF-IDF)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

vec = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), max_features=50000)
M = vec.fit_transform([c['text'] for c in CHUNKS])

def find(question, k=3):
    sim = cosine_similarity(vec.transform([question]), M)[0]
    return [(sim[i], CHUNKS[i]) for i in sim.argsort()[::-1][:k]]

def show(question, k=3):
    print('Q', question)
    for s, c in find(question, k):
        print('  %.3f [%s] %s' % (s, c['source'], c['title']))
    print()"""),

    code("""# 세 가지를 물어본다
show('연차 유급휴가는 며칠인가')
show('국가핵심기술을 해외로 유출하면 어떻게 되나')
show('개인정보를 다 쓰고 나면 어떻게 해야 하나')"""),

    md("셋 다 **관련 조문이 위쪽에 올라온다.** 질문에 쓴 말이 조문에 그대로 있기 때문이다.\n\n"
       "다만 첫 줄을 보면 「연차 유급휴가」 질문의 1등이 <b>제62조(유급휴가의 대체)</b>다.\n"
       "정답인 제60조는 2등이다. **1등이 늘 정답은 아니다** &mdash; 내일 리랭킹에서 이 문제를 다룬다."),

    Ex(2, "**낱말을 하나도 안 겹치게** 물어본다. 그러면 못 찾는다.\n"
          "> 「연차」 대신 「쉬는 날」, 「유출」 대신 「빼돌리면」 처럼 바꿔 본다.",
       setup="# 뜻은 같은데 쓰는 말이 다른 질문",
       blank="MY_Q = '___'",
       answer="MY_Q = '쉬는 날은 일 년에 며칠 받나'",
       check="show(MY_Q)"),

    md("**엉뚱한 조문이 1등으로 온다.** 「쉬는 날」과 「휴가」가 같은 뜻인 걸 이 방법은 모른다.\n"
       "글자만 보기 때문이다. 여기서 **의미로 찾는 방법**이 필요해진다."),

    md("## 4. 의미로 찾기"),
    md("문장을 **좌표**로 바꾼다. 뜻이 가까우면 좌표도 가깝다.\n"
       "모델을 하나 받아야 하는데, 노트북 안에서 도는 작은 것부터 써 본다."),

    prep("""# 임베딩 모델을 받는다. 처음 한 번만 몇 분 걸린다.
%pip install -q sentence-transformers
from sentence_transformers import SentenceTransformer
import numpy as np

EMB = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print('벡터 차원', EMB.get_sentence_embedding_dimension())"""),

    md("> 이 모델은 **내 노트북 안에서** 돈다. 문서가 밖으로 나가지 않는다.\n"
       "> 임베딩 API 를 쓰면 문서 전문이 그대로 밖으로 나간다. 사내 문서라면 그것부터 확인한다."),

    prep("""# 조각 전부를 좌표로 바꿔 둔다. 이것이 인덱싱 타임이다.
TEXTS = [c['title'] + ' ' + c['text'][:400] for c in CHUNKS]

def build(model):
    return model.encode(TEXTS, batch_size=64, normalize_embeddings=True,
                        show_progress_bar=False)

V = build(EMB)
MULTI, VM = EMB, V          # 나중에 견주려고 다국어 판을 따로 남겨 둔다
print('조각 %d개 × %d차원' % V.shape)"""),

    prep("""# 질문마다 도는 부분 — 이것이 쿼리 타임이다.
def find2(question, k=3, model=None, mat=None):
    model, mat = model or EMB, V if mat is None else mat
    q = model.encode([question], normalize_embeddings=True)[0]
    sim = mat @ q
    return [(sim[i], CHUNKS[i]) for i in sim.argsort()[::-1][:k]]

def show2(question, k=3):
    print('Q', question)
    for s, c in find2(question, k):
        print('  %.3f [%s] %s' % (s, c['source'], c['title']))
    print()"""),

    code("""# 낱말이 하나도 안 겹치는 질문 — 낱말 검색은 9등, 의미 검색은 2등에 올린다
show('일하다 위험하면 멈춰도 되나')
show2('일하다 위험하면 멈춰도 되나')"""),

    md("**「작업중지」라는 말을 한 번도 안 썼는데 찾아온다.** 뜻이 가깝기 때문이다.\n"
       "여기까지는 임베딩이 이긴다."),

    md("### 그런데 늘 이기지는 않는다"),
    md("질문 다섯 개로 두 방법을 나란히 세워 본다. **정답 조문이 몇 등에 오는지**를 센다."),

    prep("""# 정답 조문이 몇 등에 오는지 세는 자
QS = [('쉬는 날은 일 년에 며칠 받나', '제60조'),
      ('휴가를 며칠이나 쓸 수 있나', '제60조'),
      ('일하다 위험하면 멈춰도 되나', '작업중지'),
      ('직원 정보를 다 쓴 뒤에는', '제21조'),
      ('회사 기술을 외국에 팔면', '제11조')]

def rank_of(sim, needle):
    for r, i in enumerate(sim.argsort()[::-1], 1):
        if needle in CHUNKS[i]['title']:
            return r
    return None

def compare(mat, model):
    print('%-24s %6s %6s' % ('질문', '낱말', '의미'))
    for q, need in QS:
        t = rank_of(cosine_similarity(vec.transform([q]), M)[0], need)
        e = rank_of(mat @ model.encode([q], normalize_embeddings=True)[0], need)
        print('%-24s %6s %6s' % (q, t, e))"""),

    code("""compare(V, EMB)"""),

    md("**다섯 중 둘만 이긴다.** 「휴가를 며칠이나 쓸 수 있나」는 낱말 검색이 1등인데 의미 검색은 48등이다.\n"
       "이 모델이 한국어 법령 문장을 잘 못 잡는다는 뜻이다."),

    md("## 5. 모델을 바꾸면"),
    md("임베딩 모델은 **검색 품질의 천장**이다. 아무리 뒤를 손봐도 여기서 놓친 건 못 살린다.\n"
       "한국어로 학습한 모델로 바꿔서 같은 표를 다시 찍어 본다."),

    prep("""# 한국어 문장으로 학습한 모델. 조금 더 크고 조금 더 오래 걸린다.
KO = SentenceTransformer('jhgan/ko-sroberta-multitask')
VK = build(KO)
print('조각 %d개 × %d차원' % VK.shape)"""),

    code("""compare(VK, KO)"""),

    md("**다섯 개 전부 좋아진다.** 48등이던 것이 1등으로, 61등이던 것이 5등으로 올라온다.\n"
       "코드는 한 줄도 안 고쳤다. **모델 이름만 바꿨다.**"),

    Ex(3, "위 표에서 **가장 크게 달라진 질문**을 골라 두 모델의 1등을 직접 본다.",
       setup="# 같은 질문을 두 모델에 나란히 넣는다",
       blank="Q3 = '___'",
       answer="Q3 = '휴가를 며칠이나 쓸 수 있나'",
       check="""for tag, m, mat in (('다국어', MULTI, VM), ('한국어', KO, VK)):
    s, c = find2(Q3, 1, m, mat)[0]
    print('%-5s %.3f %s' % (tag, s, c['title']))"""),

    prep("""# 더 나은 쪽으로 갈아 끼운다. 아래부터는 한국어 모델로 찾는다.
EMB, V = KO, VK
print('검색기를 한국어 모델로 바꿨다')"""),

    md("### 임베딩도 못 하는 것이 있다"),

    code("""# 정확한 번호·코드는 오히려 낱말 검색이 낫다
show('제60조')
show2('제60조')"""),

    md("**번호·코드·고유명사는 낱말 검색이 이긴다.** 의미로 바꾸는 순간 「제60조」의 60이 흐려진다.\n"
       "그래서 실무에서는 **둘을 같이 돌려 순위를 합친다**. 그것이 내일 다룰 하이브리드 검색이다."),

    md("## 5. 근거로만 답하게 하기"),
    md("찾은 조각을 프롬프트에 붙이고, **그 안에서만** 답하라고 못 박는다.\n"
       "어제 쓰던 키를 그대로 쓴다."),

    prep("""# 키는 화면에 안 찍히게 받는다
import getpass
KEY = getpass.getpass('nvapi- 로 시작하는 키: ')

URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
MODEL = 'nvidia/llama-3.3-nemotron-super-49b-v1'

def ask(prompt, n=500):
    body = json.dumps({'model': MODEL, 'max_tokens': n, 'temperature': 0,
                       'messages': [{'role': 'user', 'content': prompt}]}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        'Authorization': 'Bearer ' + KEY,
        'Content-Type': 'application/json', 'Accept': 'application/json'})
    for _ in range(2):
        try:
            with urllib.request.urlopen(req, timeout=180) as f:
                return json.load(f)['choices'][0]['message']['content'].strip()
        except Exception as e:
            err = str(e)[:80]
    return '[실패] ' + err"""),

    prep("""# 찾은 조각을 붙여 물어보는 함수. RAG 는 이 열 줄이 전부다.
RULE = ('아래 「문서」에 있는 내용만 근거로 답하라.\\n'
        '문서에 없으면 "문서에 없다"고만 답하라. 아는 것으로 채우지 마라.\\n'
        '답 끝에 근거로 쓴 조문 제목을 적어라.\\n\\n')

def rag(question, k=3, log=True):
    hits = find2(question, k)
    ctx = '\\n\\n'.join('[%s] %s' % (c['source'], c['text'][:700]) for _, c in hits)
    if log:
        for s, c in hits:
            print('  [찾음 %.3f] %s' % (s, c['title']))
    return ask(RULE + '# 문서\\n' + ctx + '\\n\\n# 질문\\n' + question)"""),

    code("""# 물어본다
print(rag('연차 유급휴가는 최대 며칠까지 받을 수 있나'))"""),

    code("""# 문서에 없는 것을 물어본다 — 지어내는지 본다
print(rag('우리 회사 연차는 며칠 전에 신청해야 하나'))"""),

    md("**「문서에 없다」가 나와야 맞다.** 신청 기한은 법이 아니라 사규에 있는 내용이라,\n"
       "이 문서 묶음에는 없다. 없다고 말하게 만드는 것이 RAG 의 절반이다."),

    Ex(4, "규칙에서 **「문서에 없으면 문서에 없다고만 답하라」 한 줄을 빼고** 같은 질문을 던진다.\n"
          "> 한 줄 차이로 답이 어떻게 달라지는지 본다.",
       setup="# 근거 한정 지시를 뺀 약한 규칙",
       blank="WEAK = '아래 문서를 참고해서 답하라.\\n\\n'",
       answer="WEAK = '아래 문서를 참고해서 답하라.\\n\\n'",
       check="""q = '우리 회사 연차는 며칠 전에 신청해야 하나'
ctx = '\\n\\n'.join('[%s] %s' % (c['source'], c['text'][:700]) for _, c in find2(q, 3))
print(ask(WEAK + '# 문서\\n' + ctx + '\\n\\n# 질문\\n' + q))"""),

    md("규칙 한 줄이 빠지면 **문서 밖 지식으로 채운다**. 그럴듯해서 더 위험하다.\n"
       "프롬프트에서 가장 중요한 줄은 「없으면 없다고 하라」다."),

    md("## 6. 조각 수를 바꿔 보기"),

    code("""# k 를 바꾸면 답이 달라진다
for k in (1, 3, 6):
    print('=== k = %d' % k)
    print(rag('산업안전보건교육은 누가 받아야 하나', k=k, log=False)[:200])
    print()"""),

    md("**k 가 작으면 근거가 모자라고, 크면 상관없는 조문이 섞인다.**\n"
       "3~6 사이에서 시작해 답을 보며 조정한다. 정답은 문서마다 다르다."),

    md("## 7. 내 문서로"),
    md("여기서부터는 **자기 문서**로 바꾼다. 코드는 그대로 두고 파일만 갈아 끼운다."),

    Task(1, "자기 부서 문서를 `.txt` 로 만들어 올리고 같은 흐름을 돌린다.\n"
            "> ① Colab 왼쪽 파일 창에 `.txt` 를 올린다 → ② 아래에서 읽는다 →\n"
            "> ③ 자르고 → ④ 좌표로 바꾸고 → ⑤ 물어본다. **코드는 안 고친다.**\n"
            "> 문서를 자르는 규칙만 자기 문서에 맞게 정한다.",
         blank="""MY = open('___.txt', encoding='utf-8').read()
MY_CHUNKS = split_articles(MY, '내 문서')      # 「제N조」 규칙이 안 맞으면 아래 Task 2 로
print('조각', len(MY_CHUNKS), '개')""",
         answer="""MY = DOCS['개인정보보호법']                    # 자기 파일이 없으면 이것으로 연습한다
MY_CHUNKS = split_articles(MY, '내 문서')
print('조각', len(MY_CHUNKS), '개')""",
         check="print(MY_CHUNKS[0]['title'])"),

    Task(2, "자를 자리를 **자기 문서 규칙**으로 바꾼다.\n"
            "> 사내 문서는 「제N조」가 아니라 「1.」 「가.」 「■」 같은 표시로 나뉜다.\n"
            "> 정규식 한 줄만 바꾸면 된다. 자른 뒤 **조각 하나만 읽어서 말이 되는지** 본다.",
         blank="""PATTERN = r'___'
parts = [p.strip() for p in re.split(PATTERN, MY) if len(p.strip()) > 40]
print('조각 %d개 · 첫 조각' % len(parts))
print(parts[0][:120])""",
         answer="""PATTERN = r'\\n(?=제\\d+조)'
parts = [p.strip() for p in re.split(PATTERN, MY) if len(p.strip()) > 40]
print('조각 %d개 · 첫 조각' % len(parts))
print(parts[0][:120])""",
         check="print('조각 하나가 맥락 없이 읽혀야 검색이 산다')"),

    Task(3, "자기 문서로 **답이 틀리는 질문**을 하나 찾아 온다.\n"
            "> 틀렸을 때 원인이 셋 중 어디인지 갈라 본다.\n"
            "> ① 검색이 엉뚱한 조각을 가져왔나 → 자르는 자리·k 를 손본다\n"
            "> ② 가져왔는데 답이 틀렸나 → 프롬프트 규칙을 손본다\n"
            "> ③ 문서에 아예 없나 → 「문서에 없다」가 나오면 정상이다",
         blank="""BAD_Q = '___'
print(rag(BAD_Q))""",
         answer="""BAD_Q = '연차를 안 쓰면 돈으로 받을 수 있나'
print(rag(BAD_Q))""",
         check="print('찾은 조각 제목을 먼저 본다. 거기서 원인이 갈린다')"),

    md("### 오늘 손에 남는 것\n\n"
       "| 한 일 | 코드 |\n|---|---|\n"
       "| 문서를 읽는다 | `urlopen` · `open` |\n"
       "| 찾을 수 있게 자른다 | `re.split` 한 줄 |\n"
       "| 좌표로 바꾼다 | `EMB.encode` |\n"
       "| 가까운 것을 찾는다 | `V @ q` |\n"
       "| 근거로만 답하게 한다 | 규칙 세 줄 |\n\n"
       "**벡터 DB 도 프레임워크도 안 썼다.** 문서가 수십만 건이 되면 그때 붙인다.\n"
       "그전까지는 이 정도로 충분하고, 무엇이 어디서 갈리는지도 이 판에서 더 잘 보인다."),
]

MODES = {
    ("ex", 1): "together", ("ex", 2): "together", ("ex", 3): "together", ("ex", 4): "together",
    ("task", 1): "solo", ("task", 2): "solo", ("task", 3): "team",
}

SPEC = ("RAG — 내 문서로 답하게 하기", "실제 법령 조문으로 찾아 읽고 근거로만 답한다", CELLS, MODES)
