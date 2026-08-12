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

    md("어제 쓰던 `build.nvidia.com` 키를 그대로 쓴다. 답을 만들 때와 임베딩을 부를 때 둘 다 쓴다."),

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

    md("## 2. 자르기"),
    md("문서를 찾을 수 있는 크기로 자른다. 법령은 **조문 단위**가 자연스럽다.\n"
       "「제60조(연차 유급휴가) …」 한 덩어리가 질문 하나에 대응하기 때문이다."),

    prep("""# 자르면서 메타데이터를 같이 붙인다. 나중에 범위를 좁힐 때 쓴다.
def split_articles(text, source):
    out, chapter = [], ''
    for p in re.split(r'\\n(?=제\\d+조)', text):
        p = p.strip()
        ch = re.findall(r'^\\[제\\d+장[^\\]]*\\]', p, flags=re.M)
        if ch:
            chapter = ch[-1].strip('[]')      # 장이 바뀌면 갈아 끼운다
        if len(p) < 40:                       # 너무 짧은 조각은 버린다
            continue
        head = p.split('\\n')[0]
        num = re.match(r'제(\\d+)조', head)
        out.append({'source': source, 'chapter': chapter,
                    'article': int(num.group(1)) if num else 0,
                    'title': head[:40], 'text': p})
    return out

CHUNKS = []
for name, text in DOCS.items():
    CHUNKS += split_articles(text, name)
print('조각 %d개' % len(CHUNKS))
print('평균 %d자 · 가장 긴 것 %d자' % (sum(len(c['text']) for c in CHUNKS) / len(CHUNKS),
                                max(len(c['text']) for c in CHUNKS)))"""),

    code("""# 조각 하나에 무엇이 붙어 있는지 본다
for c in CHUNKS[40:42]:
    print('출처 %s · 장 %s · 조 %d' % (c['source'], c['chapter'], c['article']))
    print('제목 %s' % c['title'])
    print('본문 %s ...' % c['text'][:60].replace('\\n', ' '))
    print()"""),

    md("조각 하나가 **조문 하나**다. 글자 수로 잘랐다면 「제60조」의 앞뒤가 흩어졌을 것이다.\n\n"
       "본문 말고 **네 가지를 같이 적어 뒀다** &mdash; 출처 · 장 · 조 번호 · 제목.\n"
       "이것을 메타데이터라고 한다. **찾을 때 범위를 좁히고, 답할 때 근거를 대는 데** 쓴다."),

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
    md("### 「몇 등」이 무슨 뜻인가"),
    md("질문마다 **정답이 되는 조문을 미리 정해 둔다.** 「휴가를 며칠이나 쓸 수 있나」의 답은\n"
       "근로기준법 **제60조(연차 유급휴가)** 다. 사람이 미리 알고 있는 답이다.\n\n"
       "검색을 돌리면 조각 354개가 **점수 순으로 줄을 선다.** 그 줄에서 제60조가 몇 번째인지가 순위다.\n\n"
       "| 순위 | 무슨 뜻인가 |\n|---|---|\n"
       "| 1 | 정답이 맨 위에 왔다 |\n"
       "| 3 | 세 번째다. `k=3` 이면 아슬아슬하게 들어간다 |\n"
       "| 48 | **48번째다. 프롬프트에 아예 안 들어간다** |\n\n"
       "RAG 는 위에서 **k 개만** 잘라서 프롬프트에 붙인다. 보통 3~6개다.\n"
       "**정답이 48등이면 모델은 그 조문을 본 적조차 없다.** 답이 틀린 게 아니라 근거를 못 받은 것이다.\n"
       "그래서 이 숫자가 RAG 품질의 거의 전부다 &mdash; 뒤에 나올 Recall@k 가 재는 것도 같은 것이다."),

    md("질문 다섯 개로 두 방법을 나란히 세워 본다."),

    prep("""# 질문마다 정답 조문을 미리 정해 둔다. 오른쪽이 그 조문의 제목에 들어 있는 말이다.
QS = [('쉬는 날은 일 년에 며칠 받나', '제60조'),
      ('휴가를 며칠이나 쓸 수 있나', '제60조'),
      ('일하다 위험하면 멈춰도 되나', '작업중지'),
      ('직원 정보를 다 쓴 뒤에는', '제21조'),
      ('회사 기술을 외국에 팔면', '제11조')]

def rank_of(sim, needle):
    # 점수 높은 순으로 줄을 세우고, 정답 조문이 몇 번째인지 센다
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

    md("## 6. 더 큰 모델 — API 와 GPU"),
    md("앞 절까지는 **내 노트북 CPU** 에서 도는 모델만 썼다.\n"
       "더 큰 모델을 쓰는 길이 둘 있다. 하나는 **API 로 불러 쓰는 것**, 하나는 **GPU 를 켜는 것**이다."),

    md("### 길 하나 — NVIDIA API 임베딩"),
    md("모델을 안 받고 문장을 보내면 좌표를 돌려준다. 큰 모델을 그대로 쓸 수 있다.\n"
       "**다만 문장을 보낸다는 것이 곧 문서를 보낸다는 뜻이다.** 이 점은 뒤에서 다시 본다."),

    prep("""# 임베딩도 같은 키로 부른다. 주소만 다르다.
EMB_URL = 'https://integrate.api.nvidia.com/v1/embeddings'

def api_embed(model, texts, kind='passage'):
    body = json.dumps({'model': model, 'input': texts, 'input_type': kind,
                       'encoding_format': 'float', 'truncate': 'END'}).encode()
    req = urllib.request.Request(EMB_URL, data=body, headers={
        'Authorization': 'Bearer ' + KEY,
        'Content-Type': 'application/json', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as f:
        return [d['embedding'] for d in json.load(f)['data']]

def api_index(model):
    out = []
    for i in range(0, len(TEXTS), 32):          # 한 번에 서른두 개씩
        out += api_embed(model, TEXTS[i:i+32])
    v = np.array(out)
    return v / np.linalg.norm(v, axis=1, keepdims=True)

print(len(api_embed('nvidia/nv-embedqa-e5-v5', ['시험'], 'query')[0]), '차원')"""),

    prep("""# 순위를 재는 자 — 모델을 바꿔 가며 같은 다섯 질문을 던진다
def ranks(qvec_fn, mat):
    out = []
    for q, need in QS:
        sim = mat @ qvec_fn(q)
        out.append(next(r for r, i in enumerate(sim.argsort()[::-1], 1)
                        if need in CHUNKS[i]['title']))
    return out

def api_ranks(model):
    V2 = api_index(model)
    return ranks(lambda q: np.array(api_embed(model, [q], 'query')[0]) /
                 np.linalg.norm(api_embed(model, [q], 'query')[0]), V2)"""),

    code("""# 영어 중심 모델 하나와 최신 다국어 모델 하나
print('%-34s %s' % ('nv-embedqa-e5-v5', api_ranks('nvidia/nv-embedqa-e5-v5')))
print('%-34s %s' % ('nemotron-3-embed-1b', api_ranks('nvidia/nemotron-3-embed-1b')))"""),

    md("**API 라고 다 좋은 것이 아니다.**\n\n"
       "| 모델 | 어디서 | 차원 | 다섯 질문의 정답 순위 |\n|---|---|---|---|\n"
       "| 낱말 (TF-IDF) | 내 노트북 | — | 8 · 1 · 9 · 9 · 8 |\n"
       "| MiniLM 다국어 | 내 노트북 CPU | 384 | 15 · 48 · 2 · 61 · 1 |\n"
       "| ko-sroberta 한국어 | 내 노트북 CPU | 768 | **2 · 1 · 1 · 5 · 1** |\n"
       "| nv-embedqa-e5-v5 | NVIDIA API | 1024 | 82 · 7 · 229 · 28 · 75 |\n"
       "| nemotron-3-embed-1b | NVIDIA API | 2048 | **2 · 1 · 1 · 11 · 1** |\n\n"
       "`nv-embedqa-e5-v5` 는 영어 문서에 맞춰진 모델이라 한국어 법령에서 229등까지 밀린다.\n"
       "**크고 비싸다고 잘 찾는 것이 아니라, 그 언어를 배운 모델이 잘 찾는다.**"),

    md("### 그런데 문서가 밖으로 나간다"),
    md("API 로 인덱싱하면 **조각 354개가 전부 밖으로 나간다.** 문서 전체를 보낸 것과 같다.\n\n"
       "| | 내 노트북 모델 | API 모델 |\n|---|---|---|\n"
       "| 문서가 나가나 | 안 나간다 | **전부 나간다** |\n"
       "| 처음 준비 | 모델을 받는다 (몇 분) | 없다 |\n"
       "| 인덱싱 354조각 | 5초 | 25초 |\n"
       "| 질문 한 번 | 즉시 | 왕복 한 번 |\n"
       "| 비용 | 없다 | 토큰만큼 |\n\n"
       "그래서 **사내 문서는 노트북 안에서 임베딩한다.** 공개 문서나 이미 밖에 있는 자료라면 API 가 편하다.\n"
       "어느 쪽이든 **먼저 정할 것은 문서가 나가도 되느냐**다."),

    Ex(4, "API 모델을 하나 더 골라 같은 다섯 질문을 던진다.\n"
          "> `nvidia/llama-nemotron-embed-1b-v2` · `nvidia/nv-embed-v1` 중에 골라 본다.\n"
          "> 위 표에 한 줄을 더 붙인다고 생각하면 된다.",
       setup="# 모델 이름만 바꾸면 된다",
       blank="API_MODEL = '___'",
       answer="API_MODEL = 'nvidia/llama-nemotron-embed-1b-v2'",
       check="print('%-34s %s' % (API_MODEL.split('/')[-1], api_ranks(API_MODEL)))"),

    md("### 길 둘 — GPU 를 켜고 큰 모델"),
    md("Colab 메뉴에서 **런타임 → 런타임 유형 변경 → T4 GPU** 로 바꾸면 큰 모델도 돌릴 만해진다.\n"
       "문서는 여전히 **밖으로 안 나간다**. 사내 문서에 쓸 수 있는 쪽은 이쪽이다."),

    prep("""# GPU 가 잡혔는지 먼저 본다
import torch
DEV = 'cuda' if torch.cuda.is_available() else 'cpu'
print('장치', DEV, '·', torch.cuda.get_device_name(0) if DEV == 'cuda' else 'CPU 로 돌아간다')"""),

    code("""# 5억 6천만 개짜리 다국어 모델. T4 면 몇 초, CPU 면 몇 분 걸린다.
import time
BIG = SentenceTransformer('intfloat/multilingual-e5-large', device=DEV)

t0 = time.time()
VB = BIG.encode(['passage: ' + t for t in TEXTS], batch_size=32,
                normalize_embeddings=True, show_progress_bar=False)
print('%d조각 × %d차원 · %.0f초' % (*VB.shape, time.time() - t0))
print(ranks(lambda q: BIG.encode(['query: ' + q], normalize_embeddings=True)[0], VB))"""),

    md("**5억 6천만 개짜리 모델의 성적은 `1 · 2 · 1 · 11 · 1`** 이다. 한국어 모델(`2 · 1 · 1 · 5 · 1`)과 비슷하다.\n"
       "이 노트북 CPU 에서 354조각을 좌표로 바꾸는 데 **24초** 걸렸다. 조각이 만 개면 열 배가 넘는다.\n"
       "T4 를 켜면 같은 일이 몇 초로 줄어든다. **코드에서 바뀌는 것은 `device` 한 줄뿐이다.**\n\n"
       "인덱싱은 문서가 바뀔 때만 하니까 몇 분 걸려도 되지만, **질문마다 도는 부분은 빨라야 한다** &mdash;\n"
       "질문 하나를 좌표로 바꾸는 데 걸리는 시간이 곧 사용자가 기다리는 시간이다."),

    Task(5, "세 자리에서 **무엇을 고를지** 정해서 표로 적는다.\n"
            "> ① 사내 규정 문서로 사내용 검색을 만든다\n"
            "> ② 공개된 기술 문서로 사외 서비스를 만든다\n"
            "> ③ 고객 문의 로그로 내부 분석을 한다\n"
            "> 각각 **노트북 CPU · GPU · API** 중 무엇을 고르고 왜 그런지 한 줄씩.",
         blank="""ANSWER = {
    '사내 규정': '___ 를 쓴다. 왜냐하면 ___',
    '공개 기술 문서': '___ 를 쓴다. 왜냐하면 ___',
    '고객 문의 로그': '___ 를 쓴다. 왜냐하면 ___',
}
for k, v in ANSWER.items():
    print('%-12s %s' % (k, v))""",
         answer="""ANSWER = {
    '사내 규정': 'GPU 로컬 모델. 문서가 밖으로 나가면 안 된다',
    '공개 기술 문서': 'API 모델. 이미 공개된 자료라 나가도 되고 준비가 없다',
    '고객 문의 로그': 'GPU 로컬 모델. 개인정보가 섞여 있어 밖으로 못 보낸다',
}
for k, v in ANSWER.items():
    print('%-12s %s' % (k, v))""",
         check="print('성능보다 먼저 정하는 것은 문서가 나가도 되느냐다')"),

    md("## 7. 메타데이터로 범위 좁히기"),
    md("앞에서 「제60조」를 검색으로 못 찾았다. **검색으로 풀 문제가 아니었다.**\n"
       "조 번호는 이미 메타데이터에 있다. 찾는 게 아니라 **고르면** 된다."),

    code("""# 조 번호는 검색하지 않는다. 골라낸다.
hit = [c for c in CHUNKS if c['source'] == '근로기준법' and c['article'] == 60]
print(hit[0]['title'])
print(hit[0]['text'][:80])"""),

    md("### 메타데이터를 임베딩에 섞으면 되나"),
    md("출처와 장을 본문 앞에 붙여서 같이 좌표로 바꾸면 나아질 것 같다. **재 보면 아니다.**\n\n"
       "| 질문 | 제목만 | 출처+장+제목 |\n|---|---|---|\n"
       "| 쉬는 날은 일 년에 며칠 받나 | 2 | 4 |\n"
       "| 휴가를 며칠이나 쓸 수 있나 | 1 | 2 |\n"
       "| 일하다 위험하면 멈춰도 되나 | 1 | 1 |\n"
       "| 직원 정보를 다 쓴 뒤에는 | 5 | 4 |\n"
       "| 회사 기술을 외국에 팔면 | 1 | 1 |\n\n"
       "다섯 중 둘이 나빠지고 하나만 좋아졌다. **문서명·장은 질문과 상관없는 글자**라\n"
       "좌표를 흐리기만 한다. 메타데이터는 섞는 것이 아니라 **거르는 데** 쓴다."),

    prep("""# 범위를 좁혀서 찾는다. where 에 맞는 조각만 후보로 둔다.
def find3(question, k=3, where=None):
    q = EMB.encode([question], normalize_embeddings=True)[0]
    sim = V @ q
    idx = [i for i, c in enumerate(CHUNKS)
           if not where or all(c[key] == val for key, val in where.items())]
    idx.sort(key=lambda i: -sim[i])
    return [(sim[i], CHUNKS[i]) for i in idx[:k]]

def show3(question, k=3, where=None):
    print('Q %s   %s' % (question, where or '전체'))
    for s, c in find3(question, k, where):
        print('  %.3f [%s] %s' % (s, c['source'], c['title']))
    print()"""),

    code("""# 여러 법에 같은 이름의 조문이 있다
show3('비밀을 지킬 의무가 있나')
show3('비밀을 지킬 의무가 있나', where={'source': '산업기술보호법'})"""),

    md("**전체로 찾으면 1등이 개인정보 보호법 제60조**다. 산업기술 담당자가 물었다면 틀린 답이다.\n"
       "범위를 못 박으면 산업기술보호법 제34조가 온다.\n\n"
       "필터가 하는 일은 순위를 올리는 것이 아니라 **엉뚱한 문서를 후보에서 빼는 것**이다.\n"
       "문서가 늘수록, 비슷한 이름의 조항이 많을수록 이 차이가 커진다."),

    Ex(6, "**여러 문서에 다 있을 법한 질문**을 하나 만들어 전체와 좁힘을 견준다.\n"
          "> 「벌금」 「교육」 「신고」 처럼 어느 법에나 나오는 말이 좋다.",
       setup="# where 에 문서 이름을 넣으면 그 문서 안에서만 찾는다",
       blank="Q4 = '___'\nSRC = '___'",
       answer="Q4 = '위반하면 벌금이 얼마인가'\nSRC = '산업기술보호법'",
       check="show3(Q4)\nshow3(Q4, where={'source': SRC})"),

    md("실무에서는 여기에 **버전**을 하나 더 붙인다. 「최신본만」으로 걸러야\n"
       "개정 전 규정으로 답하는 사고를 막는다. 구버전이 인덱스에 남아 있으면 그걸 가져온다."),

    md("## 8. 등급과 버전으로 거르기"),
    md("사내 문서는 **아무나 다 봐도 되는 것이 아니다.** 열람 등급이 다르고, 개정본과 구버전이 섞인다.\n"
       "여기서 나는 사고는 밖으로 새는 것이 아니라 **안에서 새는 것**이다."),
    md("> 아래 등급과 시행일은 **연습을 위해 붙인 가상의 값**이다. 법령 자체에는 이런 등급이 없다.\n"
       "> 사내 문서라면 문서함의 실제 권한과 개정 이력을 그대로 옮겨 적는다."),

    prep("""# 조각마다 등급과 시행일을 붙인다. 사내에서는 문서함의 값을 그대로 옮긴다.
GRADE = {'근로기준법': 'general', '산업안전보건법': 'general',
         '개인정보보호법': 'manager', '산업기술보호법': 'restricted'}
ORDER = {'general': 0, 'manager': 1, 'restricted': 2}       # 낮을수록 널리 열람

for c in CHUNKS:
    c['clearance'] = GRADE[c['source']]
    c['effective_from'] = '2024-01-01'
    c['superseded'] = False

print({g: sum(1 for c in CHUNKS if c['clearance'] == g) for g in ORDER})"""),

    prep("""# 개정 전 조항이 인덱스에 남아 있는 상황을 만든다 (내용은 연습용으로 지어낸 것)
OLD = dict(source='근로기준법', chapter='제4장 근로시간과 휴식', article=60,
           title='제60조(연차 유급휴가) [2019년 판]',
           text='제60조(연차 유급휴가) [2019년 판] ① 사용자는 1년간 80퍼센트 이상 출근한 '
                '근로자에게 10일의 유급휴가를 주어야 한다.',
           clearance='general', effective_from='2019-01-01', superseded=True)
CHUNKS.append(OLD)
V = np.vstack([V, EMB.encode([OLD['title'] + ' ' + OLD['text']],
                             normalize_embeddings=True)])
print('조각 %d개 — 구버전 하나가 섞였다' % len(CHUNKS))"""),

    md("### 거르지 않으면"),

    code("""# 등급도 버전도 안 보고 찾는다
show3('연차 유급휴가는 며칠 받나')
show3('기술을 해외로 넘기면 어떻게 되나')"""),

    md("두 가지가 한꺼번에 드러난다.\n\n"
       "**하나** &mdash; 연차 질문의 **2등이 2019년 판**이다. 15일이 맞는데 10일짜리가 바로 밑에 붙는다.\n"
       "조각 하나만 더 가져오면 틀린 답이 섞인다.\n"
       "**둘** &mdash; 일반 직원이 물어도 **restricted 등급 조문**이 그대로 나온다."),

    prep("""# 찾기 전에 거른다. 등급과 시행일을 후보 단계에서 잘라 낸다.
def find4(question, k=3, grade='general', include_old=False):
    q = EMB.encode([question], normalize_embeddings=True)[0]
    sim = V @ q
    idx = [i for i, c in enumerate(CHUNKS)
           if ORDER[c['clearance']] <= ORDER[grade]                 # 등급
           and (include_old or not c['superseded'])]                # 버전
    idx.sort(key=lambda i: -sim[i])
    return [(sim[i], CHUNKS[i]) for i in idx[:k]]

def show4(question, k=3, grade='general'):
    print('Q %s   등급 %s' % (question, grade))
    for s, c in find4(question, k, grade):
        print('  %.3f [%-8s %s] %s' % (s, c['clearance'], c['source'], c['title']))
    print()"""),

    code("""# 같은 질문을 등급별로
show4('연차 유급휴가는 며칠 받나')
show4('기술을 해외로 넘기면 어떻게 되나', grade='general')
show4('기술을 해외로 넘기면 어떻게 되나', grade='restricted')"""),

    md("**일반 등급으로는 산업기술보호법 조문이 아예 후보에 안 든다.** 구버전도 사라졌다.\n"
       "코드에서 바뀐 것은 후보 목록을 만드는 `idx` 한 줄뿐이다."),

    md("### 왜 찾은 뒤에 거르면 안 되나"),

    code("""# 찾고 나서 거르면 몇 개가 남는지 센다
q = '기술을 해외로 넘기면 어떻게 되나'
after = [c for _, c in find4(q, 5, grade='restricted')
         if ORDER[c['clearance']] <= ORDER['general']]
print('먼저 거르면 %d개' % len(find4(q, 5, grade='general')))
print('찾고 나서 거르면 %d개' % len(after))"""),

    md("**뒤에서 거르면 손에 남는 것이 줄어든다.** 다섯 개를 찾아 놓고 등급으로 빼면 한두 개만 남는다.\n"
       "볼 수 있는 문서 중에서 다섯 개를 찾았어야 했다.\n\n"
       "게다가 **답이 늦게 오는 것만으로도** 「무언가 있긴 하다」가 새어 나간다.\n"
       "그래서 등급은 **검색 전에** 건다."),

    Ex(8, "`grade` 를 **manager** 로 두고 개인정보 질문을 던진다.\n"
          "> 일반 등급으로 물었을 때와 무엇이 달라지는지 본다.",
       setup="# 개인정보보호법은 manager 등급으로 붙여 두었다",
       blank="GRADE_TEST = '___'",
       answer="GRADE_TEST = 'manager'",
       check="""show4('개인정보를 다 쓰고 나면 어떻게 하나', grade='general')
show4('개인정보를 다 쓰고 나면 어떻게 하나', grade=GRADE_TEST)"""),

    md("## 9. 근거로만 답하게 하기"),
    md("찾은 조각을 프롬프트에 붙이고, **그 안에서만** 답하라고 못 박는다."),

    prep("""# 찾은 조각을 붙여 물어보는 함수. RAG 는 이 열 줄이 전부다.
RULE = ('아래 「문서」에 있는 내용만 근거로 답하라.\\n'
        '문서에 없으면 "문서에 없다"고만 답하라. 아는 것으로 채우지 마라.\\n'
        '답 끝에 근거로 쓴 조문 제목과 시행일을 적어라.\\n'
        '근거를 못 대면 답하지 마라.\\n\\n')

def rag(question, k=3, grade='general', log=True):
    hits = find4(question, k, grade)          # 등급·버전을 먼저 거른 뒤 찾는다
    ctx = '\\n\\n'.join('[%s %s | 시행 %s] %s'
                       % (c['source'], c['title'][:24], c['effective_from'], c['text'][:700])
                       for _, c in hits)
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

    Ex(7, "규칙에서 **「문서에 없으면 문서에 없다고만 답하라」 한 줄을 빼고** 같은 질문을 던진다.\n"
          "> 한 줄 차이로 답이 어떻게 달라지는지 본다.",
       setup="# 근거 한정 지시를 뺀 약한 규칙",
       blank="WEAK = '아래 문서를 참고해서 답하라.\\n\\n'",
       answer="WEAK = '아래 문서를 참고해서 답하라.\\n\\n'",
       check="""q = '우리 회사 연차는 며칠 전에 신청해야 하나'
ctx = '\\n\\n'.join('[%s] %s' % (c['source'], c['text'][:700]) for _, c in find2(q, 3))
print(ask(WEAK + '# 문서\\n' + ctx + '\\n\\n# 질문\\n' + q))"""),

    md("규칙 한 줄이 빠지면 **문서 밖 지식으로 채운다**. 그럴듯해서 더 위험하다.\n"
       "프롬프트에서 가장 중요한 줄은 「없으면 없다고 하라」다."),

    md("## 10. 조각 수를 바꿔 보기"),

    code("""# k 를 바꾸면 답이 달라진다
for k in (1, 3, 6):
    print('=== k = %d' % k)
    print(rag('산업안전보건교육은 누가 받아야 하나', k=k, log=False)[:200])
    print()"""),

    md("**k 가 작으면 근거가 모자라고, 크면 상관없는 조문이 섞인다.**\n"
       "3~6 사이에서 시작해 답을 보며 조정한다. 정답은 문서마다 다르다."),

    md("## 11. 내 문서로"),
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

    Task(6, "**Codex 에 시킬 프롬프트**를 쓴다. 코드가 아니라 **조건**을 적는 연습이다.\n"
            "> 아래 네 가지는 사람이 정해서 적어 줘야 한다. 안 적으면 지어낸다.\n"
            "> ① 인덱싱에서 뺄 문서 ② 등급 규칙 ③ 자르는 단위 ④ 임베딩·저장·생성이 각각 어디서\n"
            "> 특히 **「등급 필터는 검색 전에 건다」**를 안 적으면 검색 뒤에 거르는 코드가 온다.",
         blank="""MY_PROMPT = '\\n'.join([
    '# 역할', '너는 사내 규정 검색 코드를 쓰는 사람이다.', '',
    '# 넣지 않을 문서', '___', '',
    '# 등급 규칙', '___', '',
    '# 자르는 단위', '___', '',
    '# 어디서 도나', '임베딩 ___ · 벡터 저장 ___ · 생성 ___', '',
    '# 형식', '바로 돌아가는 파이썬 코드로 준다. 문서 내용을 출력하는 줄은 넣지 마라.'])
print(MY_PROMPT)""",
         answer="""MY_PROMPT = '\\n'.join([
    '# 역할', '너는 사내 규정 검색 코드를 쓰는 사람이다.', '',
    '# 넣지 않을 문서',
    '개인별 인사기록 · 급여 테이블 · 징계 개별 건 · 미확정 초안 · 서식 작성례', '',
    '# 등급 규칙',
    '조각마다 general / manager / restricted 를 붙인다.',
    '등급 필터는 반드시 검색 전에 건다. 찾은 뒤에 거르지 마라.', '',
    '# 자르는 단위',
    '조 단위로 자르고, 항으로 쪼갤 때는 조 헤더를 물려준다. 표는 쪼개지 않는다.', '',
    '# 어디서 도나', '임베딩 로컬 · 벡터 저장 사내 · 생성은 보안팀 확인 전까지 보류', '',
    '# 형식', '바로 돌아가는 파이썬 코드로 준다. 문서 내용을 출력하는 줄은 넣지 마라.'])
print(MY_PROMPT)""",
         check="print('코드는 맡기고 기준은 맡기지 않는다')"),

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
    ("ex", 1): "together", ("ex", 2): "together", ("ex", 3): "together", ("ex", 4): "solo", ("ex", 6): "solo",
    ("ex", 7): "together", ("ex", 8): "solo",
    ("task", 1): "solo", ("task", 2): "solo", ("task", 3): "team", ("task", 5): "team", ("task", 6): "team",
}

SPEC = ("RAG — 내 문서로 답하게 하기", "실제 법령 조문으로 찾아 읽고 근거로만 답한다", CELLS, MODES)
