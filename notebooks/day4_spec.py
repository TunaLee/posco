"""Day 4 — 딥러닝 실습 스펙"""
from nbkit import md, code, h, lab, Ex, Task

URL = "https://tunalee.github.io/posco/data/batch_quality.csv"

PREP = f"""import pandas as pd, numpy as np, torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

torch.manual_seed(42)

def tensors(target='양품여부'):
    df = pd.read_csv('{URL}', thousands=',', na_values=['N/A', '-'])
    df['설비호기'] = df['설비호기'].str.strip().str.upper()
    df['입도'] = df['입도'].fillna(df['입도'].median())
    df = df.dropna(subset=['수분율'])
    d = pd.get_dummies(df, columns=['설비호기', '교대조'], drop_first=True)
    X = d.drop(columns=['양품여부', '방전용량', '배치번호']).astype('float32')
    y = d[target].astype('float32')
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if target == '양품여부' else None)
    sc = StandardScaler()
    to = lambda a: torch.tensor(np.asarray(a, dtype='float32'))
    return (to(sc.fit_transform(X_tr)), to(sc.transform(X_te)),
            to(y_tr.values).unsqueeze(1), to(y_te.values).unsqueeze(1))"""

CELLS = [
    # ══════════════════════════════════════════════════════════════════
    h(2, "1. 클래스"),

    lab("클래스는 설계도, 인스턴스는 그 설계도로 만든 물건이다."),
    code("""
class Batch:
    def __init__(self, bid, temp):
        self.bid = bid
        self.temp = temp

    def is_hot(self):
        return self.temp >= 880

b = Batch("B00115", 898.9)
print(b.bid, b.temp, b.is_hot())
"""),

    Ex(1, "`Batch` 에 **최적 온도(890)에서 벗어난 정도**를 돌려주는 `gap()` 메서드를 넣는다.",
       setup="class Batch:\n"
             "    def __init__(self, bid, temp):\n"
             "        self.bid = bid\n"
             "        self.temp = temp\n",
       blank="    def gap(self):\n        return ___\n\nb = Batch('B00115', 898.9)",
       answer="    def gap(self):\n        return abs(self.temp - 890)\n\nb = Batch('B00115', 898.9)",
       check="assert abs(b.gap() - 8.9) < 1e-6, f'실제 {b.gap()}'\nprint('통과')"),

    lab("상속은 부모의 기능을 물려받고 필요한 것만 고쳐 쓴다."),
    code("""
class Machine:
    def __init__(self, name):
        self.name = name
    def describe(self):
        return f"{self.name} 설비"

class Kiln(Machine):
    def __init__(self, name, rated):
        super().__init__(name)        # 부모 초기화
        self.rated = rated
    def describe(self):               # 재정의
        return f"{self.name} 소성로 (정격 {self.rated}°C)"

print(Machine("A").describe())
print(Kiln("C", 870).describe())
"""),

    Ex(2, "`Kiln` 에 정격 온도를 넘었는지 판정하는 `over(temp)` 를 넣는다.",
       setup="class Machine:\n"
             "    def __init__(self, name):\n        self.name = name\n\n"
             "class Kiln(Machine):\n"
             "    def __init__(self, name, rated):\n"
             "        super().__init__(name)\n        self.rated = rated\n",
       blank="    def over(self, temp):\n        return ___\n\nk = Kiln('C', 870)",
       answer="    def over(self, temp):\n        return temp > self.rated\n\nk = Kiln('C', 870)",
       check="assert k.over(898) is True and k.over(850) is False, '판정이 틀렸다'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "2. 텐서"),

    lab("텐서는 NumPy 배열과 거의 같다. GPU 로 옮길 수 있고 기울기를 기억한다."),
    code("""
import torch

x = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
print(x.shape, x.dtype)
print(x * 2)
print(x @ torch.tensor([[1.], [1.], [1.]]))

print(torch.zeros(2, 3).shape)
print(x.numpy().shape)      # NumPy 로 되돌리기
"""),

    Ex(3, "`a` 를 3행 2열 텐서로 바꿔 `b` 에 담는다.",
       setup="import torch\na = torch.arange(6, dtype=torch.float32)",
       blank="b = ___",
       answer="b = a.reshape(3, 2)",
       check="assert b.shape == (3, 2), f'기대 (3, 2), 실제 {tuple(b.shape)}'\nprint('통과')"),

    lab("requires_grad 를 켜면 계산 과정을 기억했다가 기울기를 돌려준다."),
    code("""
import torch

w = torch.tensor(3.0, requires_grad=True)
loss = (w - 5) ** 2      # 최솟값은 w = 5
loss.backward()
print(w.grad)            # d(loss)/dw = 2(w-5) = -4
"""),

    Ex(4, "`w = 2.0` 일 때 `loss = (w - 7) ** 2` 의 기울기를 구해 `g` 에 담는다.",
       setup="import torch\nw = torch.tensor(2.0, requires_grad=True)",
       blank="loss = ___\nloss.backward()\ng = w.grad.item()",
       answer="loss = (w - 7) ** 2\nloss.backward()\ng = w.grad.item()",
       check="assert abs(g - (-10.0)) < 1e-6, f'기대 -10.0, 실제 {g}'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "3. 모델과 학습 루프"),

    lab("nn.Module 을 상속해 층을 쌓고, forward 에 흐르는 순서를 적는다."),
    code(f"""
{PREP}

class MLP(nn.Module):
    def __init__(self, n_in):
        super().__init__()
        self.fc1 = nn.Linear(n_in, 16)
        self.fc2 = nn.Linear(16, 1)

    def forward(self, x):
        h = torch.relu(self.fc1(x))
        return self.fc2(h)

X_tr, X_te, y_tr, y_te = tensors()
model = MLP(X_tr.shape[1])
print(model)
print(model(X_tr[:4]).shape)    # 학습 전에 shape 부터 확인한다
"""),

    Ex(5, "은닉층을 **32개**로 키운 `MLP` 를 만들고, 입력 4건을 통과시킨 출력 모양을 확인한다.",
       setup=PREP + "\nX_tr, X_te, y_tr, y_te = tensors()",
       blank="class MLP(nn.Module):\n"
             "    def __init__(self, n_in):\n"
             "        super().__init__()\n"
             "        self.fc1 = ___\n"
             "        self.fc2 = ___\n"
             "    def forward(self, x):\n"
             "        return self.fc2(torch.relu(self.fc1(x)))\n\n"
             "model = MLP(X_tr.shape[1])\nout = model(X_tr[:4])",
       answer="class MLP(nn.Module):\n"
              "    def __init__(self, n_in):\n"
              "        super().__init__()\n"
              "        self.fc1 = nn.Linear(n_in, 32)\n"
              "        self.fc2 = nn.Linear(32, 1)\n"
              "    def forward(self, x):\n"
              "        return self.fc2(torch.relu(self.fc1(x)))\n\n"
              "model = MLP(X_tr.shape[1])\nout = model(X_tr[:4])",
       check="assert tuple(out.shape) == (4, 1), f'기대 (4, 1), 실제 {tuple(out.shape)}'\n"
             "assert model.fc1.out_features == 32, '은닉층이 32여야 한다'\nprint('통과')"),

    lab("학습 루프는 다섯 줄이다. 순서가 정해져 있다."),
    code(f"""
{PREP}

class MLP(nn.Module):
    def __init__(self, n_in):
        super().__init__()
        self.fc1 = nn.Linear(n_in, 16)
        self.fc2 = nn.Linear(16, 1)
    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))

X_tr, X_te, y_tr, y_te = tensors()
model = MLP(X_tr.shape[1])
lossfn = nn.BCEWithLogitsLoss()
opt = torch.optim.Adam(model.parameters(), lr=0.01)

for epoch in range(1, 101):
    pred = model(X_tr)             # 1. 예측
    loss = lossfn(pred, y_tr)      # 2. 손실
    opt.zero_grad()                # 3. 기울기 비우기
    loss.backward()                # 4. 역전파
    opt.step()                     # 5. 갱신
    if epoch % 25 == 0:
        print(f"{{epoch:>4}}  loss {{loss.item():.4f}}")
"""),

    Ex(6, "학습 루프 **다섯 줄을 순서대로** 쓴다. 100회 돌린 뒤 손실이 줄었는지 본다.\n"
       "> 예측 → 손실 → 기울기 비우기 → 역전파 → 갱신.",
       setup=PREP + "\n"
             "class MLP(nn.Module):\n"
             "    def __init__(self, n_in):\n"
             "        super().__init__()\n"
             "        self.fc1 = nn.Linear(n_in, 16)\n"
             "        self.fc2 = nn.Linear(16, 1)\n"
             "    def forward(self, x):\n"
             "        return self.fc2(torch.relu(self.fc1(x)))\n\n"
             "X_tr, X_te, y_tr, y_te = tensors()\n"
             "model = MLP(X_tr.shape[1])\n"
             "lossfn = nn.BCEWithLogitsLoss()\n"
             "opt = torch.optim.Adam(model.parameters(), lr=0.01)\n"
             "first = None",
       blank="for epoch in range(100):\n"
             "    pred = model(X_tr)\n"
             "    loss = lossfn(pred, y_tr)\n"
             "    ___\n    ___\n    ___\n"
             "    if first is None: first = loss.item()\nlast = loss.item()",
       answer="for epoch in range(100):\n"
              "    pred = model(X_tr)\n"
              "    loss = lossfn(pred, y_tr)\n"
              "    opt.zero_grad()\n    loss.backward()\n    opt.step()\n"
              "    if first is None: first = loss.item()\nlast = loss.item()",
       check="assert last < first, f'손실이 줄어야 한다: {first:.4f} → {last:.4f}'\n"
             "print(f'통과 — {first:.4f} → {last:.4f}')"),

    Ex(7, "`opt.zero_grad()` 를 **빼면** 어떻게 되는지 본다.\n"
          "기울기가 쌓여 손실이 제대로 안 줄어드는 것을 확인한다.",
       setup=PREP + "\n"
             "class MLP(nn.Module):\n"
             "    def __init__(self, n_in):\n"
             "        super().__init__()\n"
             "        self.fc1 = nn.Linear(n_in, 16)\n"
             "        self.fc2 = nn.Linear(16, 1)\n"
             "    def forward(self, x):\n"
             "        return self.fc2(torch.relu(self.fc1(x)))\n\n"
             "X_tr, X_te, y_tr, y_te = tensors()\n"
             "model = MLP(X_tr.shape[1])\n"
             "lossfn = nn.BCEWithLogitsLoss()\n"
             "opt = torch.optim.SGD(model.parameters(), lr=0.5)\n"
             "grads = []",
       blank="for epoch in range(20):\n"
             "    loss = lossfn(model(X_tr), y_tr)\n"
             "    ___   # zero_grad 를 빼 본다\n"
             "    loss.backward()\n    opt.step()\n"
             "    grads.append(model.fc1.weight.grad.abs().mean().item())",
       answer="for epoch in range(20):\n"
              "    loss = lossfn(model(X_tr), y_tr)\n"
              "    pass   # zero_grad 를 일부러 뺀다\n"
              "    loss.backward()\n    opt.step()\n"
              "    grads.append(model.fc1.weight.grad.abs().mean().item())",
       check="assert grads[-1] > grads[0], f'기울기가 쌓여 커진다: {grads[0]:.4f} → {grads[-1]:.4f}'\n"
             "print(f'통과 — 기울기가 {grads[0]:.4f} 에서 {grads[-1]:.4f} 로 쌓였다')"),

    Task(1, "학습하면서 **손실 곡선**을 그린다.\n"
            "200회 돌리며 매 회 손실을 모아 `losses` 에 담고 그린다.",
         setup=PREP + "\nimport matplotlib.pyplot as plt\n"
               "class MLP(nn.Module):\n"
               "    def __init__(self, n_in):\n"
               "        super().__init__()\n"
               "        self.fc1 = nn.Linear(n_in, 16)\n"
               "        self.fc2 = nn.Linear(16, 1)\n"
               "    def forward(self, x):\n"
               "        return self.fc2(torch.relu(self.fc1(x)))\n\n"
               "X_tr, X_te, y_tr, y_te = tensors()\n"
               "model = MLP(X_tr.shape[1])\n"
               "lossfn = nn.BCEWithLogitsLoss()\n"
               "opt = torch.optim.Adam(model.parameters(), lr=0.01)",
         answer="losses = []\n"
                "for epoch in range(200):\n"
                "    loss = lossfn(model(X_tr), y_tr)\n"
                "    opt.zero_grad(); loss.backward(); opt.step()\n"
                "    losses.append(loss.item())\n"
                "plt.plot(losses)\nplt.xlabel('epoch'); plt.ylabel('loss'); plt.show()",
         check="assert len(losses) == 200, f'200개여야 한다: {len(losses)}'\n"
               "assert losses[-1] < losses[0] / 2, f'절반 아래로 떨어져야 한다: {losses[0]:.3f} → {losses[-1]:.3f}'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "4. 평가"),

    lab("출력은 로짓이다. 확률로 바꾸려면 시그모이드를 통과시킨다."),
    code(f"""
{PREP}

class MLP(nn.Module):
    def __init__(self, n_in):
        super().__init__()
        self.fc1 = nn.Linear(n_in, 16)
        self.fc2 = nn.Linear(16, 1)
    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))

X_tr, X_te, y_tr, y_te = tensors()
model = MLP(X_tr.shape[1])
lossfn = nn.BCEWithLogitsLoss()
opt = torch.optim.Adam(model.parameters(), lr=0.01)
for _ in range(300):
    loss = lossfn(model(X_tr), y_tr)
    opt.zero_grad(); loss.backward(); opt.step()

model.eval()
with torch.no_grad():
    prob = torch.sigmoid(model(X_te))
    pred = (prob >= 0.5).float()
    acc = (pred == y_te).float().mean().item()
print('테스트 정확도', round(acc, 3))
"""),

    Ex(8, "학습한 모델의 **테스트 정확도**를 `acc` 에 담는다.\n"
          "> `torch.no_grad()` 안에서 계산한다.",
       setup=PREP + "\n"
             "class MLP(nn.Module):\n"
             "    def __init__(self, n_in):\n"
             "        super().__init__()\n"
             "        self.fc1 = nn.Linear(n_in, 16)\n"
             "        self.fc2 = nn.Linear(16, 1)\n"
             "    def forward(self, x):\n"
             "        return self.fc2(torch.relu(self.fc1(x)))\n\n"
             "X_tr, X_te, y_tr, y_te = tensors()\n"
             "model = MLP(X_tr.shape[1])\n"
             "lossfn = nn.BCEWithLogitsLoss()\n"
             "opt = torch.optim.Adam(model.parameters(), lr=0.01)\n"
             "for _ in range(300):\n"
             "    loss = lossfn(model(X_tr), y_tr)\n"
             "    opt.zero_grad(); loss.backward(); opt.step()",
       blank="with torch.no_grad():\n    pred = ___\n    acc = ___",
       answer="with torch.no_grad():\n"
              "    pred = (torch.sigmoid(model(X_te)) >= 0.5).float()\n"
              "    acc = (pred == y_te).float().mean().item()",
       check="assert acc > 0.85, f'0.85 는 넘어야 한다: {acc}'\nprint('통과 — 정확도', round(acc, 3))"),

    Task(2, "**shape 에러를 일부러 내 보고** 메시지를 읽는다.\n"
            "입력 열 수와 `nn.Linear` 의 첫 인자를 다르게 주면 무슨 말이 나오는지 확인한다.",
         setup=PREP + "\nX_tr, X_te, y_tr, y_te = tensors()",
         answer="wrong = nn.Linear(3, 1)      # 실제 열 수는 X_tr.shape[1] 이다\n"
                "try:\n"
                "    wrong(X_tr[:4])\n"
                "except RuntimeError as e:\n"
                "    msg = str(e)\n"
                "    print(msg)\n"
                "print('실제 열 수:', X_tr.shape[1])",
         check="assert 'mat1' in msg or 'shape' in msg.lower(), f'shape 관련 메시지여야 한다: {msg}'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "5. 종합 문제"),

    Task(3, "**은닉층 크기를 바꿔 가며** 정확도를 비교한다.\n"
            "8 · 16 · 32 · 64 로 각각 300회 학습해 `results` 딕셔너리에 담고 출력한다.",
         setup=PREP + "\nX_tr, X_te, y_tr, y_te = tensors()",
         answer="def run(hidden):\n"
                "    torch.manual_seed(42)\n"
                "    class Net(nn.Module):\n"
                "        def __init__(self):\n"
                "            super().__init__()\n"
                "            self.fc1 = nn.Linear(X_tr.shape[1], hidden)\n"
                "            self.fc2 = nn.Linear(hidden, 1)\n"
                "        def forward(self, x):\n"
                "            return self.fc2(torch.relu(self.fc1(x)))\n"
                "    m = Net()\n"
                "    lossfn = nn.BCEWithLogitsLoss()\n"
                "    opt = torch.optim.Adam(m.parameters(), lr=0.01)\n"
                "    for _ in range(300):\n"
                "        loss = lossfn(m(X_tr), y_tr)\n"
                "        opt.zero_grad(); loss.backward(); opt.step()\n"
                "    with torch.no_grad():\n"
                "        pred = (torch.sigmoid(m(X_te)) >= 0.5).float()\n"
                "        return (pred == y_te).float().mean().item()\n\n"
                "results = {h: run(h) for h in (8, 16, 32, 64)}\n"
                "for k, v in results.items():\n"
                "    print(f'hidden {k:>3}  정확도 {v:.3f}')",
         check="assert len(results) == 4, f'4가지여야 한다: {results}'\n"
               "assert all(v > 0.8 for v in results.values()), f'전부 0.8 은 넘는다: {results}'\nprint('통과')"),

    Task(4, "**회귀로 바꿔 본다.** `방전용량` 을 맞히는 신경망을 만든다.\n"
            "> 마지막 층은 그대로 1개, 손실은 `nn.MSELoss()` 를 쓴다.\n"
            "> 정답 스케일이 크므로 `y` 도 표준화하면 학습이 훨씬 잘 된다.",
         setup=PREP + "\nX_tr, X_te, y_tr, y_te = tensors(target='방전용량')",
         answer="mu, sd = y_tr.mean(), y_tr.std()\n"
                "y_tr_s, y_te_s = (y_tr - mu) / sd, (y_te - mu) / sd\n\n"
                "torch.manual_seed(42)\n"
                "class Reg(nn.Module):\n"
                "    def __init__(self):\n"
                "        super().__init__()\n"
                "        self.fc1 = nn.Linear(X_tr.shape[1], 32)\n"
                "        self.fc2 = nn.Linear(32, 1)\n"
                "    def forward(self, x):\n"
                "        return self.fc2(torch.relu(self.fc1(x)))\n"
                "model = Reg()\n"
                "lossfn = nn.MSELoss()\n"
                "opt = torch.optim.Adam(model.parameters(), lr=0.01)\n"
                "for _ in range(500):\n"
                "    loss = lossfn(model(X_tr), y_tr_s)\n"
                "    opt.zero_grad(); loss.backward(); opt.step()\n\n"
                "with torch.no_grad():\n"
                "    pred = model(X_te) * sd + mu\n"
                "    rmse = ((pred - y_te) ** 2).mean().sqrt().item()\n"
                "print('RMSE', round(rmse, 2))",
         check="assert rmse < 4.0, f'RMSE 4 미만은 나온다: {rmse}'\nprint('통과')"),

    md("""
---

### 미니 프로젝트

여기까지가 나흘의 마지막이다. 남은 시간에는 **스켈레톤의 `# TODO` 여덟 곳**을 채운다.
제출물은 노트북 링크 하나이고, 기준은 점수가 아니라 **런타임 초기화 후 끝까지 도는지**다.
"""),
]

MODES = {
    # 1. 클래스
    ("ex", 1): "together", ("ex", 2): "solo",
    # 2. 텐서
    ("ex", 3): "together", ("ex", 4): "solo",
    # 3. 모델과 학습 루프
    ("ex", 5): "together", ("ex", 6): "together", ("ex", 7): "solo", ("task", 1): "team",
    # 4. 평가
    ("ex", 8): "solo", ("task", 2): "team",
    # 5. 종합
    ("task", 3): "team", ("task", 4): "team",
}

SPEC = ("딥러닝", "클래스 · 텐서 · 학습 루프 · 평가", CELLS, MODES)
