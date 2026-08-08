"""3주차 D1 — LLM 과 프롬프트 · 모델을 직접 열어 본다"""
from nbkit import md, code, h, lab, prep, Ex, Task

CELLS = [
    md("## 1. 모델을 연다"),
    md("### 준비\n\n아래 준비 셀들을 **위에서부터 차례로** 한 번씩 실행한다.\n"
       "모델을 처음 받을 때 몇 분 걸린다. **T4 GPU 로 바꿔 두면** 뒤가 빠르다."),

    prep("""# 1) 오늘 쓸 것들을 불러온다
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from transformers import AutoTokenizer, AutoModelForCausalLM
print('torch', torch.__version__)"""),

    prep("""# 2) 모델을 받아 온다 — 계수 15억 개짜리 한 대
NAME = 'Qwen/Qwen2.5-1.5B-Instruct'
tok = AutoTokenizer.from_pretrained(NAME)
# 어텐션을 꺼내 보려면 attn_implementation='eager' 여야 한다
model = AutoModelForCausalLM.from_pretrained(NAME, attn_implementation='eager')
model.eval()
print('계수 %.1f억 개' % (sum(p.numel() for p in model.parameters()) / 1e8))"""),

    prep("""# 3) 장치로 옮긴다 — cpu 면 느리지만 돌기는 한다
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
print('장치', device)"""),

    md("## 2. 토큰 — 글자도 단어도 아닌 조각"),
    code("""# 문장을 모델이 보는 단위로 쪼갠다
s = '소성로 온도가 높다'
ids = tok(s)['input_ids']
print(len(ids), '조각')
print([tok.decode([i]) for i in ids])"""),

    md("`�` 는 오류가 아니다. **글자 하나를 다 못 채운 조각**이라는 뜻이다."),

    code("""# 문장 안에서 글자 하나가 조각 몇 개가 되는지 센다
for ch in ('소', '성', '로', ' 온', '도', '가', ' 높', '다'):
    print('%-4r %d 조각' % (ch, len(tok(ch, add_special_tokens=False)['input_ids'])))"""),

    md("`온` 은 조각 둘, `높` 은 조각 셋이다. 한글은 자주 안 쓰여서 통째로 외워 둔 조각이 적다."),

    code("""# 같은 뜻인데 낱말 하나에 드는 조각 수가 다르다
for w in (' 온도', ' temperature', '소성로', ' kiln'):
    print('%-14r %d 조각' % (w, len(tok(w, add_special_tokens=False)['input_ids'])))"""),

    code("""# 그래서 같은 말을 해도 한국어가 더 비싸다
for t in ('소성로 온도가 높다', 'The kiln temperature is high'):
    print('%2d 조각   %s' % (len(tok(t)['input_ids']), t))"""),

    Ex(1, "아래 문장이 몇 조각인지 세어 `n` 에 담는다.",
       setup="q = '오늘 설비 점검에서 이상이 발견되었다'",
       blank="n = len(tok(q)['input_ids'])\nn = ___",
       answer="n = len(tok(q)['input_ids'])",
       check="print(n)\nassert isinstance(n, int) and n > 0"),

    md("## 3. 임베딩 — 토큰이 숫자 줄이 된다"),
    prep("""# 토큰 하나가 몇 칸짜리 숫자 줄인지 본다
E = model.get_input_embeddings().weight
print('어휘 %d개 · 한 토큰 %d칸' % (len(tok), E.shape[1]))
print('표는 %d줄 — 계산이 빠른 크기로 맞춰 두느라 어휘보다 조금 길다' % E.shape[0])"""),

    prep("""# 낱말 하나의 숫자 줄을 꺼내는 함수
def vec(w):
    return E[tok(w, add_special_tokens=False)['input_ids'][0]]

print('king 의 숫자 줄', tuple(vec(' king').shape))"""),

    code("""# 비슷한 뜻은 가까이 모인다 — 코사인으로 잰다
for a, b in ((' king', ' queen'), (' king', ' banana'), (' cat', ' dog')):
    print('%-9s ~%-9s  %.3f' % (a, b, F.cosine_similarity(vec(a), vec(b), dim=0).item()))"""),

    Task(1, "우리말 낱말 세 쌍을 골라 가까운 정도를 재 본다.\n"
            "> 뜻이 가까운 쌍과 먼 쌍이 숫자로 갈리는지 본다.",
         answer="""for a, b in ((' 왕', ' 여왕'), (' 왕', ' 바나나'), (' 고양이', ' 개')):
    print('%-8s ~%-8s  %.3f' % (a, b, F.cosine_similarity(vec(a), vec(b), dim=0).item()))""",
         check="print('영어보다 덜 갈릴 수 있다 — 토큰이 쪼개져서다')"),

    md("## 4. 다음 한 토큰"),
    md("모델이 하는 일은 하나다. **앞을 보고 다음 조각의 확률을 매기는 것**이다."),
    prep("""# 앞부분을 넣고 다음 조각의 점수를 받아 온다
head = '대한민국의 수도는'
x = tok(head, return_tensors='pt').to(device)
with torch.no_grad():
    logits = model(**x).logits[0, -1]
probs = logits.softmax(-1)
print('후보 %d개에 확률이 매겨졌다' % probs.shape[0])"""),

    code("""top = probs.topk(5)
for v, i in zip(top.values, top.indices):
    print('%6.2f%%   %r' % (v * 100, tok.decode([i])))"""),

    Ex(2, "1등 조각의 확률을 `p1` 에 담는다.",
       blank="p1 = probs.max().item()\np1 = ___",
       answer="p1 = probs.max().item()",
       check="print('%.4f' % p1)\nassert 0 < p1 <= 1"),

    md("## 5. 온도 — 차이를 얼마나 벌릴지"),
    code("""# 같은 점수인데 온도만 바꾼다
for T in (0.2, 1.0, 2.0):
    t3 = (logits / T).softmax(-1).topk(3)
    print('T=%.1f  ' % T,
          ['%s %.1f%%' % (tok.decode([i]), v * 100) for v, i in zip(t3.values, t3.indices)])"""),

    Task(2, "온도를 **0.1 부터 3.0 까지** 옮기며 1등 확률이 어떻게 되는지 그래프로 그린다.\n"
            "> 낮추면 1로 붙고 높이면 평평해지는 것이 보여야 한다.",
         answer="""ts = [0.1, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]
ys = [(logits / t).softmax(-1).max().item() for t in ts]
plt.plot(ts, ys, marker='o'); plt.xlabel('temperature'); plt.ylabel('1등 확률')
plt.grid(alpha=.3); plt.show()""",
         check="print('온도는 순위를 바꾸지 않는다 — 차이를 얼마나 크게 볼지만 정한다')"),

    md("## 6. 어텐션 — 어디를 보고 고르나"),
    prep("""# 어텐션 가중치를 같이 받아 온다
s2 = 'The bank of the river was very steep'
x2 = tok(s2, return_tensors='pt').to(device)
with torch.no_grad():
    out = model(**x2, output_attentions=True)
A = out.attentions
print('층 %d개 · 층마다 머리 %d개 · 토큰 %d개' % (len(A), A[0].shape[1], A[0].shape[-1]))"""),

    code("""# 한 머리가 실제로 본 곳을 그림으로
L, H = 14, 0
w = A[L][0, H].float().cpu()
labels = [tok.decode([i]) for i in x2['input_ids'][0]]

plt.figure(figsize=(6, 5))
plt.imshow(w, cmap='Purples')
plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
plt.yticks(range(len(labels)), labels)
plt.title('%d층 %d번 머리' % (L, H)); plt.colorbar(); plt.show()"""),

    Task(3, "층과 머리를 바꿔 가며 그려 본다.\n"
            "> 앞 층은 옆 토큰을, 뒤 층은 멀리 있는 토큰을 보는 경향이 있는지 확인한다.",
         answer="""fig, ax = plt.subplots(1, 3, figsize=(13, 4))
for a, (L, H) in zip(ax, [(0, 0), (14, 0), (26, 3)]):
    a.imshow(A[L][0, H].float().cpu(), cmap='Purples')
    a.set_title('%d층 %d번' % (L, H)); a.set_xticks([]); a.set_yticks([])
plt.show()""",
         check="print('머리마다 보는 자리가 다르다')"),

    md("## 7. 프롬프트는 앞부분이다"),
    md("대화창에 `messages` 로 넣는 것도 결국 **글자 한 줄**이 된다. 직접 찍어 본다."),

    code("""# 채팅 틀이 실제로 어떤 글자가 되는지 본다
chat = [{'role': 'system', 'content': '너는 제철소 설비 기술자다.'},
        {'role': 'user', 'content': '고로가 뭐야?'}]
print(tok.apply_chat_template(chat, tokenize=False, add_generation_prompt=True))"""),

    md("`system` 도 `user` 도 특별한 통로가 아니다. **한 줄로 이어 붙는 앞부분**일 뿐이다.\n"
       "그래서 프롬프트를 바꾸는 일은 곧 다음 토큰의 확률을 옮기는 일이 된다."),

    prep("""# 앞으로 쓸 답 만들기 함수 — 채팅 틀을 씌워 이어 쓰게 한다
def gen(user, system=None, n=56):
    ms = ([{'role': 'system', 'content': system}] if system else []) \\
         + [{'role': 'user', 'content': user}]
    p = tok.apply_chat_template(ms, tokenize=False, add_generation_prompt=True)
    x = tok(p, return_tensors='pt').to(device)
    with torch.no_grad():
        y = model.generate(**x, max_new_tokens=n, do_sample=False)
    return tok.decode(y[0][x['input_ids'].shape[1]:], skip_special_tokens=True)"""),

    md("### 형식을 못 박으면"),
    prep("""# 오늘 물어볼 한 문장
ask = '설비 점검에서 소음이 크고 진동이 있다.'
print(ask)"""),

    code("""# 그냥 물어본다
print(gen(ask))"""),

    code("""# 답의 모양을 지정해서 다시 물어본다
form = ask + '\\n아래 형식으로만 답하라.\\n증상: \\n의심 원인: \\n조치: '
print(gen(form))"""),

    Ex(3, "칸 이름을 하나 더 넣어(`재발 방지:`) 다시 돌려 `out` 에 담는다.",
       setup="form2 = ask + '\\n아래 형식으로만 답하라.\\n증상: \\n의심 원인: \\n조치: \\n재발 방지: '",
       blank="out = gen(___, n=120)",
       answer="out = gen(form2, n=120)",
       check="print(out)\nassert '재발' in out"),

    md("### 예시를 붙이면"),
    code("""# 답의 모양을 말로 설명하는 대신 예시 두 줄로 보여 준다
few = ('아래 형식을 따라 답하라.\\n'
       '입력: 베어링 온도 92도 → 판정: 이상 / 근거: 기준 80도 초과\\n'
       '입력: 진동 2.1mm/s → 판정: 정상 / 근거: 기준 4.5mm/s 이내\\n'
       '입력: 소음 88dB → ')
print('[예시 없이]', gen('입력: 소음 88dB → ', n=40))
print('[예시 붙여]', gen(few, n=40))"""),

    md("형식은 그대로 따라온다. 그런데 **근거로 나온 기준값은 준 적이 없는 숫자**다.\n"
       "형식은 잡히고 판단은 잡히지 않는다는 것이 여기서 그대로 드러난다."),

    md("### 지어내는 자리"),
    code("""# 모델이 모르는 말을 물어본다
print(gen('고로가 뭐야?', n=40))"""),

    Task(4, "현장에서 쓰는 설비 이름 세 개를 물어보고 답이 맞는지 본다.\n"
            "> 틀린 답을 얼마나 자신 있게 말하는지 함께 확인한다.",
         answer="""for w in ('고로', '전로', '소성로'):
    print('[%s] %s\\n' % (w, gen('%s가 뭐야? 한 문장으로 답해라.' % w, n=40)))""",
         check="print('모르면 비운 채 두지 않고 그럴듯한 말을 채워 넣는다')"),

    md("프롬프트는 **앞부분을 바꿔 확률을 옮기는 일**이다.\n"
       "형식과 말투는 이걸로 잡히지만, **없는 지식은 만들어 내지 못한다**."),
]

MODES = {
    ("ex", 1): "together", ("task", 1): "solo",
    ("ex", 2): "together", ("task", 2): "solo",
    ("task", 3): "solo",
    ("ex", 3): "together", ("task", 4): "team",
}

SPEC = ("LLM 과 프롬프트", "모델을 직접 열어 토큰 · 확률 · 어텐션을 본다", CELLS, MODES)
