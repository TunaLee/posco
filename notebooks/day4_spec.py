"""Day 4 — 딥러닝 실습 스펙 · 손글씨 숫자(MNIST)와 동물 사진(CIFAR-10)"""
from nbkit import md, code, h, lab, prep, Ex, Task

PREP = """import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

torch.manual_seed(42)

train = datasets.MNIST('data', train=True,  download=True, transform=transforms.ToTensor())
test  = datasets.MNIST('data', train=False, download=True, transform=transforms.ToTensor())
loader      = DataLoader(train, batch_size=128, shuffle=True)
test_loader = DataLoader(test,  batch_size=1000)"""

FIT = '''def fit(model, ld=None, epochs=3, lr=0.001):
    """학습 루프 다섯 줄을 함수로 묶어 둔 것"""
    ld = ld if ld is not None else loader
    torch.manual_seed(42)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(epochs):
        for xb, yb in ld:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
    return model

def score(model, ld=None):
    """학습에 안 쓴 자료로 재는 정확도"""
    ld = ld if ld is not None else test_loader
    correct = total = 0
    with torch.no_grad():
        for xb, yb in ld:
            correct += (model(xb).argmax(1) == yb).sum().item()
            total += len(yb)
    return correct / total'''

CELLS = [
    # ══════════════════════════════════════════════════════════════════
    h(2, "1. 이미지를 텐서로"),

    md("### 준비\n\n아래 셀을 **먼저 한 번** 실행한다. 자료를 받고 학습·평가 함수를 만든다.\n"
       "내려받기와 기본 모델 학습까지 1분쯤 걸린다."),
    prep(PREP + "\n\n" + FIT + """

model = nn.Sequential(
    nn.Flatten(),
    nn.Linear(784, 128), nn.ReLU(),
    nn.Linear(128, 64),  nn.ReLU(),
    nn.Linear(64, 10))
model = fit(model, epochs=3)
xb, yb = next(iter(loader))
print('준비 끝 — 기본 모델 정확도', round(score(model), 4))"""),

    lab("받아 온 자료를 들여다본다."),
    code("""
x, y = train[0]
print(len(train), len(test))
print(x.shape, x.dtype, y)
print(x.min().item(), x.max().item())"""),

    Ex(1, "그림 한 장을 **글자로 찍어 본다.** 밝기가 0.5 를 넘는 칸은 `#`, 나머지는 공백으로 28줄을 출력한다.",
       setup="x, y = train[0]\na = x[0]",
       blank="for r in range(28):\n    print(''.join('#' if ___ else ' ' for c in range(28)))",
       answer="for r in range(28):\n    print(''.join('#' if a[r, c] > 0.5 else ' ' for c in range(28)))",
       check="print('정답은', y)"),

    Ex(2, "`x` 를 **한 줄로 펴서** `flat` 에 담고 모양을 확인한다.",
       setup="x, y = train[0]",
       blank="flat = ___",
       answer="flat = x.flatten()",
       check="assert tuple(flat.shape) == (784,), f'기대 (784,), 실제 {tuple(flat.shape)}'\nprint('통과 —', flat.shape)"),

    Ex(3, "`loader` 에서 배치 하나를 꺼내 `xb`, `yb` 에 담고 모양을 본다.",
       blank="xb, yb = ___",
       answer="xb, yb = next(iter(loader))",
       check="assert tuple(xb.shape) == (128, 1, 28, 28), f'실제 {tuple(xb.shape)}'\n"
             "print('입력', tuple(xb.shape), '· 정답', tuple(yb.shape))"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "2. 모델 만들기"),

    lab("층을 순서대로 적기만 하면 모델이 된다. 준비 셀에서 만든 model 이 이 모양이다."),
    code("""
print(model)
print('계수', sum(p.numel() for p in model.parameters()))"""),

    Ex(4, "**층 하나짜리** 모델을 만들어 `flat_model` 에 담는다. 펴고 나서 곧바로 열 갈래로 보낸다.",
       blank="flat_model = ___",
       answer="flat_model = nn.Sequential(nn.Flatten(), nn.Linear(784, 10))",
       check="assert flat_model(xb).shape == (128, 10), f'실제 {tuple(flat_model(xb).shape)}'\n"
             "print('계수', sum(p.numel() for p in flat_model.parameters()))"),

    Ex(5, "**활성화 함수를 뺀** 모델을 만들어 `no_relu` 에 담는다. 층은 셋 그대로 두고 `nn.ReLU()` 만 없앤다.",
       blank="no_relu = ___",
       answer="no_relu = nn.Sequential(nn.Flatten(),\n"
              "                        nn.Linear(784, 128),\n"
              "                        nn.Linear(128, 64),\n"
              "                        nn.Linear(64, 10))",
       check="names = [type(m).__name__ for m in no_relu]\n"
             "assert 'ReLU' not in names, '아직 ReLU 가 있다'\n"
             "assert names.count('Linear') == 3, f'Linear 가 셋이어야 한다: {names}'\nprint('통과 —', names)"),

    lab("흐름에 손을 대야 할 때는 nn.Module 을 상속해 forward 에 직접 쓴다."),
    code("""
class Net(nn.Module):
    def __init__(self, hidden=128):
        super().__init__()
        self.fc1 = nn.Linear(784, hidden)
        self.fc2 = nn.Linear(hidden, 10)

    def forward(self, x):
        x = x.flatten(1)
        return self.fc2(torch.relu(self.fc1(x)))

net = Net()
print(net(xb).shape)"""),

    Ex(6, "`Net2` 에 **은닉층을 하나 더** 넣는다. 784 → 128 → 64 → 10 이 되게 `fc3` 까지 쓴다.",
       setup="class Net2(nn.Module):\n    def __init__(self):\n        super().__init__()",
       blank="        self.fc1 = nn.Linear(784, 128)\n        ___\n        ___\n\n"
             "    def forward(self, x):\n        x = x.flatten(1)\n        ___\n        ___\n        ___\n\n"
             "net2 = Net2()",
       answer="        self.fc1 = nn.Linear(784, 128)\n"
              "        self.fc2 = nn.Linear(128, 64)\n"
              "        self.fc3 = nn.Linear(64, 10)\n\n"
              "    def forward(self, x):\n        x = x.flatten(1)\n"
              "        x = torch.relu(self.fc1(x))\n"
              "        x = torch.relu(self.fc2(x))\n"
              "        return self.fc3(x)\n\n"
              "net2 = Net2()",
       check="assert net2(xb).shape == (128, 10), f'실제 {tuple(net2(xb).shape)}'\n"
             "n = sum(p.numel() for p in net2.parameters())\n"
             "assert n == 109386, f'계수가 109,386개여야 한다: {n}'\nprint('통과 — 계수 109,386개')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "3. 학습"),

    lab("다섯 줄이 한 걸음이다. 배치가 469개니 1 에폭에 469 걸음이다."),
    code("""
print('배치', len(loader), '개 · 3 에폭이면', len(loader) * 3, '걸음')
print('준비 셀에서 이미 3 에폭 돌렸다 — 정확도', round(score(model), 4))"""),

    Ex(7, "**학습 루프 다섯 줄을 순서대로** 쓴다. 층 하나짜리 `one` 을 1 에폭 돌린 뒤 마지막 손실을 찍는다.\n"
          "> 비우기 → 예측 → 손실 → 역전파 → 갱신.",
       setup="one = nn.Sequential(nn.Flatten(), nn.Linear(784, 10))\n"
             "opt = torch.optim.Adam(one.parameters(), lr=0.001)\n"
             "loss_fn = nn.CrossEntropyLoss()\n\n"
             "for xb2, yb2 in loader:",
       blank="    ___\n    ___\n    ___\n    ___\n    ___\n\nprint('마지막 손실', round(loss.item(), 4))",
       answer="    opt.zero_grad()\n"
              "    pred = one(xb2)\n"
              "    loss = loss_fn(pred, yb2)\n"
              "    loss.backward()\n"
              "    opt.step()\n\n"
              "print('마지막 손실', round(loss.item(), 4))",
       check="acc = score(one)\nassert acc > 0.85, f'0.85 는 넘어야 한다: {acc}'\n"
             "print('통과 — 층 하나짜리 정확도', round(acc, 4))"),

    Ex(8, "**`opt.zero_grad()` 를 빼면** 기울기가 쌓이는 것을 눈으로 본다. 다섯 회차의 기울기 크기를 찍는다.",
       setup="probe = nn.Sequential(nn.Flatten(), nn.Linear(784, 10))\n"
             "opt2 = torch.optim.SGD(probe.parameters(), lr=0.1)\n"
             "loss_fn = nn.CrossEntropyLoss()\n"
             "it = iter(DataLoader(train, batch_size=128))\n\n"
             "for k in range(5):\n    xb3, yb3 = next(it)",
       blank="    loss_fn(probe(xb3), yb3).backward()\n"
             "    print(k + 1, '회차 기울기 크기', round(___, 1))\n    opt2.step()",
       answer="    loss_fn(probe(xb3), yb3).backward()\n"
              "    print(k + 1, '회차 기울기 크기', round(probe[1].weight.grad.abs().sum().item(), 1))\n"
              "    opt2.step()",
       check="print('회차마다 커지면 쌓이고 있는 것이다')"),

    Task(1, "**손실 곡선**을 그린다. 층 하나짜리 모델을 새로 만들어 1 에폭 돌리며 매 걸음의 손실을 `losses` 에 모은다.\n"
            "> 469개 점이 찍힌다. 가파르게 떨어지다 완만해지는 모양이면 정상이다.",
         answer="import matplotlib.pyplot as plt\n\n"
                "torch.manual_seed(42)\n"
                "m = nn.Sequential(nn.Flatten(), nn.Linear(784, 10))\n"
                "opt3 = torch.optim.Adam(m.parameters(), lr=0.001)\n"
                "loss_fn = nn.CrossEntropyLoss()\n"
                "losses = []\n"
                "for xb4, yb4 in loader:\n"
                "    opt3.zero_grad()\n"
                "    l = loss_fn(m(xb4), yb4)\n"
                "    l.backward(); opt3.step()\n"
                "    losses.append(l.item())\n\n"
                "plt.plot(losses)\n"
                "plt.xlabel('step'); plt.ylabel('loss')\n"
                "plt.show()",
         check="assert len(losses) == len(loader), f'걸음 수가 {len(losses)} 다'\n"
               "assert losses[-1] < losses[0], '손실이 줄지 않았다'\nprint('통과 — 걸음', len(losses))"),

    Task(2, "**학습률 세 가지**로 1 에폭씩 돌려 비교한다. `0.00001` · `0.001` · `0.5` 를 써서 정확도를 `by_lr` 에 담는다.\n"
            "> 너무 작으면 못 가고 너무 크면 발산한다.",
         answer="by_lr = {}\n"
                "for lr in (0.00001, 0.001, 0.5):\n"
                "    torch.manual_seed(42)\n"
                "    m = nn.Sequential(nn.Flatten(), nn.Linear(784, 10))\n"
                "    by_lr[lr] = round(score(fit(m, epochs=1, lr=lr)), 4)\n"
                "print(by_lr)",
         check="assert by_lr[0.001] > by_lr[0.00001], '0.001 이 더 나아야 한다'\n"
               "print('가장 나은 학습률', max(by_lr, key=by_lr.get))"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "4. 평가와 진단"),

    lab("정확도는 학습에 안 쓴 1만 장으로 잰다. no_grad 로 감싼다."),
    code("""
print('은닉 둘 + ReLU', round(score(model), 4))
print('층 하나       ', round(score(flat_model), 4))"""),

    Ex(9, "**활성화 함수가 없으면** 층을 쌓아도 소용없다는 것을 확인한다.\n"
      "> 앞에서 만든 `no_relu` 와 `flat_model` 을 쓴다. 3 에폭 돌려 정확도를 `acc_no_relu` 에 담는다.",
       blank="acc_no_relu = ___",
       answer="acc_no_relu = score(fit(no_relu, epochs=3))",
       check="print('활성화 없음', round(acc_no_relu, 4))\n"
             "print('층 하나  ', round(score(flat_model), 4))\n"
             "print('둘이 비슷하면 쌓기만 해서는 얻는 것이 없다는 뜻이다')"),

    Task(3, "**무엇을 무엇으로 착각하는지** 센다. 테스트 1만 장에서 틀린 짝을 세어 가장 잦은 다섯 개를 찍는다.\n"
            "> `(실제, 예측)` 을 열쇠로 세면 된다.",
         answer="conf = {}\n"
                "with torch.no_grad():\n"
                "    for xb5, yb5 in test_loader:\n"
                "        pred = model(xb5).argmax(1)\n"
                "        for a, b in zip(yb5.tolist(), pred.tolist()):\n"
                "            if a != b:\n"
                "                conf[(a, b)] = conf.get((a, b), 0) + 1\n\n"
                "print('오답', sum(conf.values()), '/ 10000')\n"
                "top = sorted(conf.items(), key=lambda kv: -kv[1])[:5]\n"
                "for (a, b), cnt in top:\n"
                "    print(f'{a} 인데 {b} 라고 — {cnt}건')",
         check="assert sum(conf.values()) < 800, '오답이 너무 많다'\nprint('통과')"),

    Task(4, "**shape 에러를 일부러 내 보고** 메시지를 읽는다. 입력 칸 수를 784 가 아니라 28 로 적은 모델에 배치를 넣는다.\n"
            "> 괄호 안의 네 숫자만 본다. 가운데 둘이 안 맞아서 나는 에러다.",
         answer="bad = nn.Sequential(nn.Flatten(), nn.Linear(28, 128))\n"
                "try:\n"
                "    bad(xb)\n"
                "except RuntimeError as e:\n"
                "    print(e)",
         check="print('128x784 와 28x128 — 가운데 784 와 28 이 달라서 난 에러다')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "5. 동물 사진으로 갈아 끼우기"),

    md("CIFAR-10 은 32×32 컬러 사진 6만 장이다. 열 갈래 중 여섯이 동물이다.\n\n"
       "아래 셀을 **먼저 한 번** 실행한다. 170MB 를 받으므로 30초쯤 걸린다."),
    prep("""c_train = datasets.CIFAR10('data', train=True,  download=True, transform=transforms.ToTensor())
c_test  = datasets.CIFAR10('data', train=False, download=True, transform=transforms.ToTensor())
c_loader      = DataLoader(c_train, batch_size=128, shuffle=True)
c_test_loader = DataLoader(c_test,  batch_size=1000)

print(c_train.classes)
print('한 장', c_train[0][0].shape, '→ 펴면 3 × 32 × 32 =', 3 * 32 * 32, '칸')"""),

    Ex(11, "동물 사진 **한 장을 그려 본다.**\n"
           "> 토치는 `[3, 32, 32]` 로 담는데 `imshow` 는 `[32, 32, 3]` 을 원한다. 축 순서를 바꿔야 한다.",
        setup="import matplotlib.pyplot as plt\n\nimg, lab = c_train[0]\nprint(img.shape)",
        blank="plt.imshow(___)\nplt.title(c_train.classes[lab])\nplt.axis('off')\nplt.show()",
        answer="plt.imshow(img.permute(1, 2, 0))\nplt.title(c_train.classes[lab])\nplt.axis('off')\nplt.show()",
        check="print('정답은', c_train.classes[lab])"),

    Ex(10, "MNIST 에 쓰던 모델을 **입력 칸 수만 바꿔** 동물용으로 만든다. `animal` 에 담는다.\n"
           "> 3 × 32 × 32 가 몇 칸인지 먼저 세어 본다.",
        blank="animal = nn.Sequential(\n    nn.Flatten(),\n    nn.Linear(___, 128), nn.ReLU(),\n"
              "    nn.Linear(128, 64),  nn.ReLU(),\n    nn.Linear(64, 10))",
        answer="animal = nn.Sequential(\n    nn.Flatten(),\n    nn.Linear(3072, 128), nn.ReLU(),\n"
               "    nn.Linear(128, 64),  nn.ReLU(),\n    nn.Linear(64, 10))",
        check="cb, _ = next(iter(c_loader))\n"
              "assert animal(cb).shape == (128, 10), f'실제 {tuple(animal(cb).shape)}'\n"
              "print('통과 — 계수', sum(p.numel() for p in animal.parameters()))"),

    Task(5, "**동물 사진으로 학습시켜** 정확도를 `acc_animal` 에 담고 손글씨 숫자와 비교한다. 3 에폭이면 충분하다.\n"
            "> `fit` 과 `score` 에 동물용 로더를 넘겨 준다.",
         answer="animal = fit(animal, c_loader, epochs=3)\n"
                "acc_animal = score(animal, c_test_loader)\n"
                "print('동물 사진  ', round(acc_animal, 4))\n"
                "print('손글씨 숫자', round(score(model), 4))",
         check="assert 0.2 < acc_animal < 0.7, f'0.2~0.7 사이가 나와야 한다: {acc_animal}'\n"
               "print('숫자보다 한참 낮다 — 왜 그럴까')"),

    Task(7, "**열 갈래를 한 장씩** 뽑아 격자로 그린다. 2행 5열로 늘어놓고 각 사진 위에 갈래 이름을 적는다.\n"
            "> 아직 못 본 갈래가 나오면 담아 두는 식으로 열 장을 모으면 된다.",
         answer="import matplotlib.pyplot as plt\n\n"
                "seen = {}\n"
                "for img, lab in c_train:\n"
                "    if lab not in seen:\n"
                "        seen[lab] = img\n"
                "    if len(seen) == 10:\n"
                "        break\n\n"
                "fig, axes = plt.subplots(2, 5, figsize=(9, 4))\n"
                "for ax, lab in zip(axes.flat, sorted(seen)):\n"
                "    ax.imshow(seen[lab].permute(1, 2, 0))\n"
                "    ax.set_title(c_train.classes[lab], fontsize=9)\n"
                "    ax.axis('off')\n"
                "plt.show()",
         check="assert len(seen) == 10, f'열 갈래를 다 모아야 한다: {len(seen)}'\nprint('통과 — 열 장')"),

    Task(6, "**은닉층을 키워도 크게 안 오르는 것**을 확인한다. 128·64 를 512·256 으로 늘려 3 에폭 돌린 뒤 앞의 정확도와 견준다.\n"
            "> 계수가 몇 배 늘어도 점수는 조금 오른다. 펴는 순간 이웃 정보를 잃기 때문이다.",
         answer="big = nn.Sequential(\n"
                "    nn.Flatten(),\n"
                "    nn.Linear(3072, 512), nn.ReLU(),\n"
                "    nn.Linear(512, 256),  nn.ReLU(),\n"
                "    nn.Linear(256, 10))\n"
                "big = fit(big, c_loader, epochs=3)\n"
                "acc_big = score(big, c_test_loader)\n"
                "print('작은 모델', round(acc_animal, 4), '· 계수', sum(p.numel() for p in animal.parameters()))\n"
                "print('큰 모델  ', round(acc_big, 4),    '· 계수', sum(p.numel() for p in big.parameters()))",
         check="assert acc_big - acc_animal < 0.06, '차이가 이렇게 크면 다시 확인한다'\n"
               "print('계수가 네 배인데 점수는 1%p 도 안 오른다')\n"
               "print('펴서 넣는 방식의 한계다 — 다음 단계는 이웃 픽셀을 묶어 보는 CNN 이다')"),

    Task(8, "**틀린 사진을 눈으로 본다.** 학습한 `animal` 이 틀린 것 여덟 장을 골라, 실제 갈래와 모델의 답을 제목에 적어 그린다.\n"
            "> 사람이 봐도 헷갈릴 짝인지 살펴본다.",
         answer="import matplotlib.pyplot as plt\n\n"
                "wrong = []\n"
                "with torch.no_grad():\n"
                "    for xb, yb in c_test_loader:\n"
                "        pred = animal(xb).argmax(1)\n"
                "        for i in range(len(yb)):\n"
                "            if pred[i] != yb[i] and len(wrong) < 8:\n"
                "                wrong.append((xb[i], yb[i].item(), pred[i].item()))\n"
                "        if len(wrong) == 8:\n"
                "            break\n\n"
                "fig, axes = plt.subplots(2, 4, figsize=(9, 5))\n"
                "for ax, (img, real, said) in zip(axes.flat, wrong):\n"
                "    ax.imshow(img.permute(1, 2, 0))\n"
                "    ax.set_title(f'{c_train.classes[real]} → {c_train.classes[said]}', fontsize=8)\n"
                "    ax.axis('off')\n"
                "plt.show()",
         check="assert len(wrong) == 8, f'여덟 장을 모아야 한다: {len(wrong)}'\n"
               "for _, real, said in wrong:\n"
               "    print(f'{c_train.classes[real]:10s} 인데 {c_train.classes[said]} 라고')"),
]

MODES = {
    # 1. 이미지를 텐서로
    ("ex", 1): "together", ("ex", 2): "together", ("ex", 3): "solo",
    # 2. 모델 만들기
    ("ex", 4): "together", ("ex", 5): "solo", ("ex", 6): "team",
    # 3. 학습
    ("ex", 7): "together", ("ex", 8): "solo", ("task", 1): "solo", ("task", 2): "team",
    # 4. 평가와 진단
    ("ex", 9): "together", ("task", 3): "solo", ("task", 4): "solo",
    # 5. 동물 사진
    ("ex", 11): "together", ("ex", 10): "together", ("task", 7): "solo",
    ("task", 5): "team", ("task", 6): "team", ("task", 8): "team",
}

SPEC = ("딥러닝", "손글씨 숫자로 배우고 동물 사진으로 확인한다", CELLS, MODES)
