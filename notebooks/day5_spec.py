"""2주차 D1 — 이미지 분류 실습 스펙 · 합성곱과 전이학습(CIFAR-10)"""
from nbkit import md, code, h, lab, prep, Ex, Task

PREP = """import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

torch.manual_seed(42)

train = datasets.CIFAR10('data', train=True,  download=True, transform=transforms.ToTensor())
test  = datasets.CIFAR10('data', train=False, download=True, transform=transforms.ToTensor())

# 5,000장만 떼어 쓴다. Subset 은 데이터에서 일부만 골라 주는 것이다.
# 전체 5만 장으로 돌리면 한 번에 몇 분씩 걸려 여러 번 비교하기 어렵다.
small      = Subset(train, range(5000))
small_test = Subset(test,  range(1000))
loader      = DataLoader(small,      batch_size=128, shuffle=True)
test_loader = DataLoader(small_test, batch_size=500)

names = train.classes
print(names)"""

FIT = '''def fit(model, ld=None, epochs=6, lr=0.001):
    """학습 루프 다섯 줄을 함수로 묶어 둔 것 — 1주차에 만든 것과 같다"""
    ld = ld if ld is not None else loader
    torch.manual_seed(42)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    model.train()
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
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for xb, yb in ld:
            correct += (model(xb).argmax(1) == yb).sum().item()
            total += len(yb)
    return correct / total

def count(model):
    """배울 계수가 몇 개인지"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)'''

CELLS = [
    # ══════════════════════════════════════════════════════════════════
    h(2, "1. 필터를 직접 통과시켜 본다"),

    md("### 준비\n\n아래 두 셀을 **먼저 한 번** 실행한다. 자료를 받고 학습·평가 함수를 만든다.\n"
       "CIFAR-10 은 163MB 라 내려받기에 1~2분 걸린다.\n\n"
       "이미 드라이브에 받아 둔 파일이 있으면 아래 세 줄을 먼저 실행한다.\n\n"
       "```python\n"
       "from google.colab import drive; drive.mount('/content/drive')\n"
       "!mkdir -p data && cp '/content/drive/MyDrive/cifar-10-python.tar.gz' data/\n"
       "```"),
    prep(PREP),
    prep(FIT),

    md("사진 한 장이 어떤 모양인지부터 본다."),
    prep("""img, label = test[13]
print('모양   ', img.shape)
print('이름   ', names[label])
print('값 범위', float(img.min()), '~', float(img.max()))

plt.imshow(img.permute(1, 2, 0))   # imshow 는 [행, 열, 색] 순서를 원한다
plt.axis('off'); plt.show()

# 색 세 면의 평균으로 흑백 한 장을 만들어 둔다. 필터 실습에서 이것을 쓴다.
gray = img.mean(0)
print('흑백 모양', gray.shape)"""),

    Ex(1, "`img` 에서 **빨강 면 하나만** 꺼내 `red` 에 담는다. 모양이 `[3, 32, 32]` 이고 "
          "0번 축이 색이므로 그 축의 0번을 고른다.",
       blank="red = img[___]",
       answer="red = img[0]",
       check="print(red.shape)\n"
             "assert tuple(red.shape) == (32, 32), f'32x32 여야 한다: {tuple(red.shape)}'\n"
             "plt.imshow(red, cmap='Reds'); plt.axis('off'); plt.show()"),

    md("### 합성곱 한 층 만들기\n\n"
       "`nn.Conv2d(들어오는 채널, 필터 장수, 창 크기, padding=1)` 네 자리를 채우면 된다."),

    Ex(2, "컬러 사진(채널 3)을 받아 **특징 지도 32장**을 내놓는 합성곱 층을 만든다. "
          "창은 3×3, `padding=1` 로 가로세로를 유지한다.",
       blank="conv = nn.Conv2d(___, ___, ___, padding=1)",
       answer="conv = nn.Conv2d(3, 32, 3, padding=1)",
       check="out = conv(img.unsqueeze(0))   # unsqueeze(0) 은 사진 한 장을 배치 하나로 감싸는 것\n"
             "print(out.shape)\n"
             "assert tuple(out.shape) == (1, 32, 32, 32), f'[1,32,32,32] 여야 한다: {tuple(out.shape)}'"),

    md("### 필터의 아홉 수를 사람이 정해 본다\n\n"
       "`conv.weight` 가 필터 뭉치다. `conv.weight.data[0, 0]` 은 **0번 필터가 빨강 면에 쓰는 3×3** 이다.\n"
       "여기에 값을 직접 넣으면 학습에 맡기지 않고 우리가 정한 무늬를 찾게 할 수 있다."),

    prep("""def apply_filter(k, image=None):
    \"\"\"3x3 필터 하나를 흑백 사진에 통과시켜 결과를 돌려준다\"\"\"
    image = image if image is not None else gray
    c = nn.Conv2d(1, 1, 3, padding=1, bias=False)
    c.weight.data[0, 0] = torch.tensor(k, dtype=torch.float)
    with torch.no_grad():
        return c(image.view(1, 1, 32, 32))[0, 0]

vert = apply_filter([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
print('세로 윤곽선 범위 %+.0f ~ %+.0f' % (vert.min() * 255, vert.max() * 255))"""),

    Ex(3, "**가로 윤곽선**을 찾는 필터를 적어 `horz` 에 담는다. 세로 필터가 좌우로 `-1 0 +1` 이었으니, "
          "가로는 **위아래로** 같은 모양을 쓴다.",
       blank="horz = apply_filter([[-1, -1, -1],\n"
             "                     [ ___,  ___,  ___],\n"
             "                     [ ___,  ___,  ___]])",
       answer="horz = apply_filter([[-1, -1, -1],\n"
              "                     [ 0,  0,  0],\n"
              "                     [ 1,  1,  1]])",
       check="print(horz.shape)\n"
             "assert tuple(horz.shape) == (32, 32)\n"
             "assert horz.abs().max() > 0.3, '값이 거의 0이면 필터가 잘못 적힌 것이다'"),

    Task(1, "세로 · 가로 · 흐리게 세 결과를 원본과 함께 **한 줄에 네 장**으로 그린다. "
            "흐리게 필터는 아홉 칸 모두 `1/9` 이다. 그림 제목에 무엇인지 적는다.",
         answer="blur = apply_filter([[1/9] * 3] * 3)\n\n"
                "fig, axes = plt.subplots(1, 4, figsize=(11, 3))\n"
                "for ax, (t, im) in zip(axes, [('원본', gray), ('세로', vert.abs()),\n"
                "                              ('가로', horz.abs()), ('흐리게', blur)]):\n"
                "    ax.imshow(im, cmap='gray')\n"
                "    ax.set_title(t); ax.axis('off')\n"
                "plt.show()",
         check="assert 'blur' in dir(), 'blur 를 만들어야 한다'\n"
               "print('세로가 남긴 양 %.1f · 가로가 남긴 양 %.1f' % (vert.abs().sum(), horz.abs().sum()))"),

    Ex(4, "`padding` 을 **0** 으로 바꾸면 가로세로가 어떻게 되는지 확인한다. "
          "창이 사진 안에만 들어가야 하므로 양쪽 한 줄씩 못 쓴다.",
       blank="c0 = nn.Conv2d(3, 8, 3, padding=___)\n"
             "print(c0(img.unsqueeze(0)).shape)",
       answer="c0 = nn.Conv2d(3, 8, 3, padding=0)\n"
              "print(c0(img.unsqueeze(0)).shape)",
       check="s = tuple(c0(img.unsqueeze(0)).shape)\n"
             "assert s == (1, 8, 30, 30), f'[1,8,30,30] 이어야 한다: {s}'\n"
             "print('32 였던 것이', s[2], '가 됐다')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "2. shape 를 따라간다"),

    md("`Conv2d` 는 **채널**을 바꾸고 `MaxPool2d` 는 **가로세로**를 절반으로 만든다.\n"
       "이 두 규칙만 알면 마지막 `Linear` 의 입력 칸 수를 세지 않고 얻을 수 있다."),

    Ex(5, "`Conv2d` → `ReLU` → `MaxPool2d` 한 묶음을 통과시킨 뒤 모양을 찍는다. "
          "채널은 3에서 16으로, 가로세로는 32에서 절반이 된다.",
       blank="block = nn.Sequential(\n"
             "    nn.Conv2d(3, 16, 3, padding=1),\n"
             "    nn.ReLU(),\n"
             "    nn.MaxPool2d(___))\n"
             "print(block(img.unsqueeze(0)).shape)",
       answer="block = nn.Sequential(\n"
              "    nn.Conv2d(3, 16, 3, padding=1),\n"
              "    nn.ReLU(),\n"
              "    nn.MaxPool2d(2))\n"
              "print(block(img.unsqueeze(0)).shape)",
       check="s = tuple(block(img.unsqueeze(0)).shape)\n"
             "assert s == (1, 16, 16, 16), f'[1,16,16,16] 이어야 한다: {s}'"),

    Task(2, "묶음을 **세 번** 쌓으면 가로세로가 몇이 되는지 코드로 확인한다. "
            "채널은 3 → 16 → 32 → 64 로 두껍게 만든다. 마지막에 `Flatten()` 을 붙여 "
            "**몇 칸이 되는지** 찍는다.",
         answer="deep = nn.Sequential(\n"
                "    nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
                "    nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
                "    nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
                "    nn.Flatten())\n"
                "print(deep(img.unsqueeze(0)).shape)",
         check="n = deep(img.unsqueeze(0)).shape[1]\n"
               "assert n == 64 * 4 * 4, f'64*4*4 = 1024 여야 한다: {n}'\n"
               "print('32 → 16 → 8 → 4 이므로 64 x 4 x 4 =', n)"),

    Ex(6, "`MaxPool2d` 를 빼고 `Flatten` 뒤에 `Linear(64*8*8, 10)` 을 붙이면 에러가 난다. "
          "일부러 내 보고 **메시지의 네 숫자**를 읽는다.",
       blank="bad = nn.Sequential(\n"
             "    nn.Conv2d(3, 64, 3, padding=1), nn.ReLU(),\n"
             "    nn.Flatten(),\n"
             "    nn.Linear(64 * 8 * 8, 10))\n"
             "try:\n"
             "    bad(img.unsqueeze(0))\n"
             "except RuntimeError as e:\n"
             "    msg = ___\n"
             "    print(msg)",
       answer="bad = nn.Sequential(\n"
              "    nn.Conv2d(3, 64, 3, padding=1), nn.ReLU(),\n"
              "    nn.Flatten(),\n"
              "    nn.Linear(64 * 8 * 8, 10))\n"
              "try:\n"
              "    bad(img.unsqueeze(0))\n"
              "except RuntimeError as e:\n"
              "    msg = str(e)\n"
              "    print(msg)",
       check="assert 'msg' in dir() and 'shapes cannot be multiplied' in msg, '에러가 나야 정상이다'\n"
             "print('들어온 칸 수 65536 · 적어 둔 칸 수 4096 — 풀링을 빼서 절반으로 줄지 않았다')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "3. CNN 을 만들어 돌린다"),

    md("먼저 1주차 방식(펴서 `Linear`)을 같은 데이터로 재 둔다. 비교 기준이 필요하다."),

    md("### 준비 · 비교 기준\n\n"
       "모델을 만들 때마다 `torch.manual_seed(42)` 를 **먼저** 부른다. "
       "계수의 첫 값이 난수로 정해지므로, 이것을 고정하지 않으면 돌릴 때마다 정확도가 달라진다."),
    prep("""torch.manual_seed(42)
mlp = nn.Sequential(nn.Flatten(), nn.Linear(3072, 128), nn.ReLU(), nn.Linear(128, 10))
fit(mlp)
print('펴서 Linear  정확도 %.4f  계수 %d' % (score(mlp), count(mlp)))

# 비교 기준이 될 CNN 도 미리 한 벌 만들어 둔다. 아래 문제들이 이것과 견준다.
torch.manual_seed(42)
cnn = nn.Sequential(
    nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
    nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
    nn.Flatten(),
    nn.Linear(64 * 8 * 8, 10))
fit(cnn)
print('CNN          정확도 %.4f  계수 %d' % (score(cnn), count(cnn)))"""),

    Ex(7, "준비 셀의 CNN 을 **직접 다시 써서** `my_cnn` 을 만든다. 채널은 3 → 32 → 64, "
          "가로세로는 32 → 16 → 8 이므로 마지막 `Linear` 의 입력은 `64*8*8` 이다. "
          "학습까지 시켜 준비 셀과 같은 값이 나오는지 본다.",
       blank="torch.manual_seed(42)\n"
             "my_cnn = nn.Sequential(\n"
             "    nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
             "    nn.Conv2d(___, ___, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
             "    nn.Flatten(),\n"
             "    nn.Linear(___, 10))\n"
             "fit(my_cnn)\n"
             "print('정확도 %.4f  계수 %d' % (score(my_cnn), count(my_cnn)))",
       answer="torch.manual_seed(42)\n"
              "my_cnn = nn.Sequential(\n"
              "    nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
              "    nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
              "    nn.Flatten(),\n"
              "    nn.Linear(64 * 8 * 8, 10))\n"
              "fit(my_cnn)\n"
              "print('정확도 %.4f  계수 %d' % (score(my_cnn), count(my_cnn)))",
       check="assert count(my_cnn) == 60362, f'계수가 60,362 여야 한다: {count(my_cnn)}'\n"
             "assert score(my_cnn) == score(cnn), '준비 셀과 같은 값이 나와야 한다'\n"
             "print('계수는 %d 분의 1 인데 정확도는 올랐다' % (count(mlp) // count(my_cnn)))"),

    Task(3, "묶음 **하나**짜리 CNN 도 만들어 셋을 나란히 비교한다. `계수 · 정확도` 를 함께 찍는다. "
            "묶음이 하나면 가로세로가 16 이므로 `Linear` 의 입력은 `32*16*16` 이다.",
         answer="torch.manual_seed(42)\n"
                "one = nn.Sequential(\n"
                "    nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
                "    nn.Flatten(),\n"
                "    nn.Linear(32 * 16 * 16, 10))\n"
                "fit(one)\n\n"
                "for t, m in [('펴서 Linear', mlp), ('묶음 하나', one), ('묶음 둘', cnn)]:\n"
                "    print('%-12s 계수 %7d   정확도 %.4f' % (t, count(m), score(m)))",
         check="assert 'one' in dir(), 'one 을 만들어야 한다'\n"
               "print('묶음 하나가 계수는 더 많다 — 펴는 칸이 8192 라서다')\n"
               "print('정확도는 둘이 거의 같다. 5,000장에서는 깊이의 값이 아직 안 나온다')"),

    Task(4, "필터 장수를 **16장**과 **64장**으로 바꿔 묶음 둘짜리 CNN 을 두 개 더 만든다. "
            "`계수 · 정확도 · 걸린 시간` 세 값을 표로 찍는다. 시간은 `time.time()` 으로 잰다.",
         setup="import time",
         answer="rows = []\n"
                "for k in (16, 32, 64):\n"
                "    torch.manual_seed(42)\n"
                "    m = nn.Sequential(\n"
                "        nn.Conv2d(3, k, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
                "        nn.Conv2d(k, k * 2, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
                "        nn.Flatten(),\n"
                "        nn.Linear(k * 2 * 8 * 8, 10))\n"
                "    t0 = time.time()\n"
                "    fit(m)\n"
                "    rows.append((k, count(m), score(m), time.time() - t0))\n\n"
                "for k, n, a, s in rows:\n"
                "    print('필터 %2d장  계수 %7d  정확도 %.4f  %4.0f초' % (k, n, a, s))",
         check="assert len(rows) == 3, '세 줄이 나와야 한다'\n"
               "assert rows[0][1] < rows[2][1], '필터가 많으면 계수도 많다'"),

    Task(5, "가장 많이 **틀린 두 종류**를 찾는다. 종류마다 몇 장 중 몇 장을 맞혔는지 세어 "
            "정확도가 낮은 순으로 찍는다.",
         answer="hit = [0] * 10\n"
                "tot = [0] * 10\n"
                "cnn.eval()\n"
                "with torch.no_grad():\n"
                "    for xb, yb in test_loader:\n"
                "        pred = cnn(xb).argmax(1)\n"
                "        for i in range(len(yb)):\n"
                "            tot[yb[i]] += 1\n"
                "            hit[yb[i]] += int(pred[i] == yb[i])\n\n"
                "rank = sorted(range(10), key=lambda c: hit[c] / tot[c])\n"
                "for c in rank:\n"
                "    print('%-10s %3d / %3d   %.3f' % (names[c], hit[c], tot[c], hit[c] / tot[c]))",
         check="assert sum(tot) == 1000, f'1,000장을 다 세야 한다: {sum(tot)}'\n"
               "print('가장 어려운 둘:', names[rank[0]], '·', names[rank[1]])"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "4. 이미 배운 모델을 가져온다"),

    md("### 사전학습 모델 받기\n\n"
       "`resnet18` 은 사진 128만 장으로 학습이 끝난 모델이다. "
       "`weights='DEFAULT'` 가 **학습된 계수까지 함께** 받아 온다는 뜻이다."),

    prep("""from torchvision import models

net = models.resnet18(weights='DEFAULT')
print('전체 계수', sum(p.numel() for p in net.parameters()))
print('마지막 층 ', net.fc)"""),

    Ex(8, "마지막 층을 **10 종류짜리**로 갈아 끼운다. 입력 칸 수 `512` 는 앞쪽 층이 내놓는 값이라 바꿀 수 없다.",
       blank="net.fc = nn.Linear(___, ___)\n"
             "print(net.fc)\n"
             "print('새 층의 계수', sum(p.numel() for p in net.fc.parameters()))",
       answer="net.fc = nn.Linear(512, 10)\n"
              "print(net.fc)\n"
              "print('새 층의 계수', sum(p.numel() for p in net.fc.parameters()))",
       check="n = sum(p.numel() for p in net.fc.parameters())\n"
             "assert n == 5130, f'512*10+10 = 5,130 이어야 한다: {n}'"),

    md("### 얼린 앞쪽으로 특징만 뽑는다\n\n"
       "앞쪽 층을 학습시키지 않으면 그 출력은 **몇 번 통과시켜도 같다**. "
       "그러니 한 번만 통과시켜 512칸을 저장해 두고, 그 다음부터는 512칸으로만 학습한다.\n\n"
       "`resnet18` 은 224×224 로 학습됐고 색마다 평균을 빼는 정규화를 쓴다. "
       "**학습 때와 같은 형식으로 먹여야** 배운 것이 제대로 나온다."),

    prep("""T224 = transforms.Compose([
    transforms.Resize(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

big_train = datasets.CIFAR10('data', train=True,  transform=T224)
big_test  = datasets.CIFAR10('data', train=False, transform=T224)

backbone = models.resnet18(weights='DEFAULT')
backbone.fc = nn.Identity()      # 마지막 층을 없애는 대신 그대로 내놓게 한다
backbone.eval()

def features(ds, n):
    \"\"\"사진 n 장을 얼린 앞쪽에 한 번 통과시켜 512칸씩 뽑아 둔다\"\"\"
    X, Y = [], []
    with torch.no_grad():
        for xb, yb in DataLoader(Subset(ds, range(n)), batch_size=64):
            X.append(backbone(xb)); Y.append(yb)
    return torch.cat(X), torch.cat(Y)

# 6,000장을 224x224 로 한 번 통과시킨다. GPU 면 30초, CPU 면 몇 분 걸린다.
# 런타임 유형을 GPU 로 바꿔 두면 훨씬 빠르다.
Xtr, Ytr = features(big_train, 5000)
Xte, Yte = features(big_test,  1000)
print(Xtr.shape, Xte.shape)"""),

    md("뽑아 둔 512칸으로 **선형 분류기 하나만** 학습시키는 함수를 만들어 둔다.\n"
       "사진이 아니라 숫자 512칸이므로 30에폭을 돌려도 몇 초면 끝난다.\n\n"
       "새로 나오는 두 가지가 있다.\n\n"
       "- `torch.cat(리스트)` — 배치마다 나온 결과를 **한 덩이로 붙인다**. "
       "위 `features` 함수가 이것으로 512칸들을 모았다.\n"
       "- `torch.randperm(n)` — `0`부터 `n-1`까지를 **뒤섞은 순서**를 만든다. "
       "`DataLoader` 의 `shuffle=True` 가 안에서 하던 일을 직접 하는 것이다. "
       "에폭마다 순서를 바꿔야 같은 순서로 외우는 일이 없다."),
    prep("""def train_head(X, Y, epochs=30, Xv=None, Yv=None):
    \"\"\"512칸으로 Linear(512, 10) 하나만 학습시켜 (모델, 정확도) 를 돌려준다\"\"\"
    Xv = Xv if Xv is not None else Xte
    Yv = Yv if Yv is not None else Yte
    torch.manual_seed(42)
    h = nn.Linear(512, 10)
    o = torch.optim.Adam(h.parameters(), lr=0.001)
    f = nn.CrossEntropyLoss()
    for _ in range(epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 128):
            b = perm[i:i + 128]
            o.zero_grad()
            f(h(X[b]), Y[b]).backward()
            o.step()
    with torch.no_grad():
        return h, (h(Xv).argmax(1) == Yv).float().mean().item()

head, acc = train_head(Xtr, Ytr)
print('전이학습 정확도 %.4f  학습한 계수 %d' % (acc, count(head)))"""),

    Ex(9, "준비 셀의 `train_head` 안쪽 루프를 **직접 써서** `my_head` 를 학습시킨다. "
          "1주차 학습 루프 다섯 줄과 같고, 사진 대신 `Xtr` 의 512칸을 먹인다는 점만 다르다.",
       blank="torch.manual_seed(42)\n"
             "my_head = nn.Linear(512, 10)\n"
             "opt = torch.optim.Adam(my_head.parameters(), lr=0.001)\n"
             "loss_fn = nn.CrossEntropyLoss()\n\n"
             "for e in range(30):\n"
             "    perm = torch.randperm(len(Xtr))\n"
             "    for i in range(0, len(Xtr), 128):\n"
             "        b = perm[i:i + 128]\n"
             "        opt.___()                          # 기울기를 비운다\n"
             "        loss_fn(my_head(Xtr[b]), Ytr[b]).___()   # 기울기를 구한다\n"
             "        opt.___()                          # 한 걸음 옮긴다\n\n"
             "with torch.no_grad():\n"
             "    my_acc = (my_head(Xte).argmax(1) == Yte).float().mean().item()\n"
             "print('%.4f  학습한 계수 %d' % (my_acc, count(my_head)))",
       answer="torch.manual_seed(42)\n"
              "my_head = nn.Linear(512, 10)\n"
              "opt = torch.optim.Adam(my_head.parameters(), lr=0.001)\n"
              "loss_fn = nn.CrossEntropyLoss()\n\n"
              "for e in range(30):\n"
              "    perm = torch.randperm(len(Xtr))\n"
              "    for i in range(0, len(Xtr), 128):\n"
              "        b = perm[i:i + 128]\n"
              "        opt.zero_grad()                          # 기울기를 비운다\n"
              "        loss_fn(my_head(Xtr[b]), Ytr[b]).backward()   # 기울기를 구한다\n"
              "        opt.step()                          # 한 걸음 옮긴다\n\n"
              "with torch.no_grad():\n"
              "    my_acc = (my_head(Xte).argmax(1) == Yte).float().mean().item()\n"
              "print('%.4f  학습한 계수 %d' % (my_acc, count(my_head)))",
       check="assert count(my_head) == 5130, f'512*10+10 = 5,130 이어야 한다: {count(my_head)}'\n"
             "assert abs(my_acc - acc) < 1e-6, f'준비 셀과 같아야 한다: {my_acc} 대 {acc}'\n"
             "print('계수 5,130개로 %.4f — CNN 60,362개보다 적게 배우고 더 맞혔다' % my_acc)"),

    Task(6, "훈련 장수를 **5,000 · 2,000 · 500 · 200** 으로 줄여 가며 전이학습 정확도를 잰다. "
            "이미 뽑아 둔 `Xtr` 의 앞쪽만 잘라 쓰면 특징을 다시 뽑을 필요가 없다.",
         answer="for n in (5000, 2000, 500, 200):\n"
                "    _, a = train_head(Xtr[:n], Ytr[:n])\n"
                "    print('훈련 %4d장  전이학습 %.4f' % (n, a))",
         check="_, a200 = train_head(Xtr[:200], Ytr[:200])\n"
               "print('5,000장 %.4f → 200장 %.4f · 25분의 1로 줄여도 얼마나 버티는지 본다' % (acc, a200))"),

    Task(7, "같은 **200장**으로 CNN 을 처음부터 학습시켜 전이학습과 나란히 비교한다. "
            "`Subset(train, range(200))` 으로 작은 loader 를 만들어 쓴다.",
         answer="tiny = DataLoader(Subset(train, range(200)), batch_size=32, shuffle=True)\n"
                "torch.manual_seed(42)\n"
                "scratch = nn.Sequential(\n"
                "    nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
                "    nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),\n"
                "    nn.Flatten(),\n"
                "    nn.Linear(64 * 8 * 8, 10))\n"
                "fit(scratch, tiny, epochs=20)\n"
                "print('200장 · CNN 처음부터   %.4f  계수 %d' % (score(scratch), count(scratch)))\n"
                "print('200장 · 전이학습       %.4f  계수 %d' % (train_head(Xtr[:200], Ytr[:200])[1], 5130))",
         check="assert 'scratch' in dir(), 'scratch 를 만들어야 한다'\n"
               "print('사진이 적을 때 어느 쪽이 쓸 만한지가 이 실습의 결론이다')"),

    Ex(10, "정규화를 **빼면** 얼마나 떨어지는지 본다. `Resize` 와 `ToTensor` 만 쓴 형식으로 "
           "특징을 다시 뽑아 같은 방식으로 학습한다. 에러는 나지 않으니 숫자로만 알 수 있다.",
        blank="T_no = transforms.Compose([\n"
              "    transforms.Resize(224),\n"
              "    transforms.ToTensor()])          # Normalize 를 뺐다\n\n"
              "raw_train = datasets.CIFAR10('data', train=True,  transform=___)\n"
              "raw_test  = datasets.CIFAR10('data', train=False, transform=___)\n"
              "Xr, Yr = features(raw_train, 5000)\n"
              "Xs, Ys = features(raw_test,  1000)",
        answer="T_no = transforms.Compose([\n"
               "    transforms.Resize(224),\n"
               "    transforms.ToTensor()])          # Normalize 를 뺐다\n\n"
               "raw_train = datasets.CIFAR10('data', train=True,  transform=T_no)\n"
               "raw_test  = datasets.CIFAR10('data', train=False, transform=T_no)\n"
               "Xr, Yr = features(raw_train, 5000)\n"
               "Xs, Ys = features(raw_test,  1000)",
        check="_, bad_acc = train_head(Xr, Yr, Xv=Xs, Yv=Ys)\n"
              "print('정규화 있음 %.4f · 없음 %.4f' % (acc, bad_acc))\n"
              "assert bad_acc < acc, '정규화를 빼면 떨어져야 한다'"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "5. 세 방식을 한 표로"),

    Task(8, "오늘 만든 세 방식을 **한 표**로 정리해 찍는다. `방식 · 학습한 계수 · 정확도` 세 칸이다. "
            "전이학습은 테스트 500장, 나머지는 1,000장이라 조건이 다른 것을 표 아래에 적는다.",
         answer="print('%-22s %10s %10s' % ('방식', '학습 계수', '정확도'))\n"
                "print('-' * 44)\n"
                "print('%-22s %10d %10.4f' % ('펴서 Linear', count(mlp), score(mlp)))\n"
                "print('%-22s %10d %10.4f' % ('CNN 처음부터', count(cnn), score(cnn)))\n"
                "print('%-22s %10d %10.4f' % ('resnet18 특징 + Linear', 5130, acc))\n"
                "print()\n"
                "print('훈련 5,000장 · 테스트 1,000장 — 세 방식 모두 같은 조건이다')",
         check="print('계수는 줄고 정확도는 오른다 — 이것이 오늘의 결론이다')"),

    Task(9, "전이학습이 **틀린 사진 여섯 장**을 골라 `실제 → 예측` 을 제목으로 붙여 그린다. "
            "`big_test` 의 사진은 정규화돼 있어 그대로 그리면 색이 이상하니 `test` 에서 같은 번호를 가져온다.",
         answer="with torch.no_grad():\n"
                "    pred = head(Xte).argmax(1)\n\n"
                "wrong = [i for i in range(len(Yte)) if pred[i] != Yte[i]][:6]\n\n"
                "fig, axes = plt.subplots(1, 6, figsize=(13, 3))\n"
                "for ax, i in zip(axes, wrong):\n"
                "    ax.imshow(test[i][0].permute(1, 2, 0))\n"
                "    ax.set_title('%s → %s' % (names[Yte[i]], names[pred[i]]), fontsize=9)\n"
                "    ax.axis('off')\n"
                "plt.show()",
         check="assert len(wrong) == 6, f'여섯 장을 골라야 한다: {len(wrong)}'\n"
               "for i in wrong:\n"
               "    print('%-10s 인데 %s 라고' % (names[Yte[i]], names[pred[i]]))"),

    Task(10, "오늘 새로 배운 다섯 줄을 각각 **한 문장으로** 설명하는 주석을 달아 셀에 적는다. "
             "`nn.Conv2d` · `nn.MaxPool2d` · `models.resnet18` · `requires_grad` · `net.fc` 대입.",
         answer="# nn.Conv2d(3, 32, 3, padding=1)\n"
                "#   3x3 창을 미끄러뜨려 무늬를 찾는다. 채널이 3에서 32로 두꺼워진다.\n"
                "# nn.MaxPool2d(2)\n"
                "#   겹치지 않는 2x2 마다 최댓값 하나만 남긴다. 가로세로가 절반이 된다.\n"
                "# models.resnet18(weights='DEFAULT')\n"
                "#   사진 128만 장으로 학습이 끝난 계수까지 함께 받아 온다.\n"
                "# p.requires_grad = False\n"
                "#   그 계수의 기울기를 구하지 않는다. 학습에서 움직이지 않는다.\n"
                "# net.fc = nn.Linear(512, 10)\n"
                "#   마지막 층만 내 문제 크기로 갈아 끼운다. 앞쪽은 그대로 쓴다.\n"
                "print('정리 끝')",
         check="print('이 다섯 줄이 오늘 늘어난 전부다')"),
]

MODES = {
    # 1. 필터를 직접 통과시켜 본다
    ("ex", 1): "together", ("ex", 2): "together", ("ex", 3): "solo",
    ("task", 1): "solo", ("ex", 4): "together",
    # 2. shape 를 따라간다
    ("ex", 5): "together", ("task", 2): "solo", ("ex", 6): "together",
    # 3. CNN 을 만들어 돌린다
    ("ex", 7): "together", ("task", 3): "solo", ("task", 4): "team", ("task", 5): "team",
    # 4. 이미 배운 모델을 가져온다
    ("ex", 8): "together", ("ex", 9): "together", ("task", 6): "solo",
    ("task", 7): "team", ("ex", 10): "solo",
    # 5. 세 방식을 한 표로
    ("task", 8): "together", ("task", 9): "solo", ("task", 10): "team",
}

SPEC = ("이미지 분류", "합성곱으로 만들고 남이 배운 것을 가져온다", CELLS, MODES)
