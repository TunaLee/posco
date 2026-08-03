"""2주차 D2 — 내 데이터로 분류기 · 객체탐지 · 파인튜닝 · 추적"""
from nbkit import md, code, h, lab, prep, Ex, Task

PREP = """# ── 준비 ──────────────────────────────────────────────────────────────
# 런타임 → 런타임 유형 변경 → T4 GPU 로 바꾸고 시작한다
import os, sys, time, glob, torch, torch.nn as nn
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print('장치', device)
if device == 'cuda':
    print(torch.cuda.get_device_name(0))

# 자료 — 드라이브 폴더를 먼저 보고, 없으면 원래 자리에서 받는다
DRIVE_ZIP = ''      # 강사가 알려 주는 파일 ID 를 넣으면 드라이브에서 받는다
if not os.path.isdir('hymenoptera_data'):
    if DRIVE_ZIP:
        os.system(f'{sys.executable} -m pip install -q gdown')
        os.system(f'gdown {DRIVE_ZIP} -O hym.zip -q')
    if not os.path.isfile('hym.zip'):
        os.system('wget -q https://download.pytorch.org/tutorial/hymenoptera_data.zip -O hym.zip')
    os.system('unzip -q hym.zip')

NORM = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
T = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224),
                        transforms.ToTensor(), NORM])
train = datasets.ImageFolder('hymenoptera_data/train', T)
val   = datasets.ImageFolder('hymenoptera_data/val', T)
print(train.classes, len(train), len(val))"""

FEAT = """# 얼린 resnet18 으로 사진을 512칸으로 바꿔 둔다 — 한 번만 하면 된다
net = models.resnet18(weights='DEFAULT')
net.fc = nn.Identity()
net.eval().to(device)

def feats(ds):
    X, Y = [], []
    with torch.no_grad():
        for xb, yb in DataLoader(ds, batch_size=32):
            X.append(net(xb.to(device)).cpu()); Y.append(yb)
    return torch.cat(X), torch.cat(Y)

t0 = time.time()
Xtr, Ytr = feats(train)
Xva, Yva = feats(val)
print('%.1f초 · %s %s' % (time.time() - t0, tuple(Xtr.shape), tuple(Xva.shape)))

def train_head(X, Y, epochs=30, seed=42):
    torch.manual_seed(seed)
    head = nn.Linear(512, 2)
    opt = torch.optim.Adam(head.parameters(), lr=0.001)
    loss_fn = nn.CrossEntropyLoss()
    for e in range(epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 32):
            b = perm[i:i + 32]
            opt.zero_grad(); loss_fn(head(X[b]), Y[b]).backward(); opt.step()
    return head

def acc(head, X, Y):
    with torch.no_grad():
        return (head(X).argmax(1) == Y).float().mean().item()"""

YOLO_PREP = """# 탐지 — 오픈 가중치를 받아 그대로 써 본다
os.system(f'{sys.executable} -m pip install -q ultralytics')
from ultralytics import YOLO

if not os.path.isfile('bus.jpg'):
    os.system('wget -q https://ultralytics.com/images/bus.jpg')
det = YOLO('yolo11n.pt')
print('아는 종류', len(det.names), '개 · 계수',
      sum(p.numel() for p in det.model.parameters()))"""

CELLS = [
    md("## 1. 사진을 512칸으로 바꾼다"),
    md("### 준비\n\n아래 두 셀을 **먼저 한 번** 실행한다. "
       "런타임을 **T4 GPU** 로 바꾼 뒤에 실행해야 뒤가 빠르다."),
    prep(PREP),
    prep(FEAT),

    md("사진 한 장이 512칸이 된 것을 직접 본다."),
    code("""v = Xtr[0]
print('512칸 중 앞 12개')
print([round(float(x), 2) for x in v[:12]])
print('최소 %.2f · 최대 %.2f · 0 인 칸 %d개' % (v.min(), v.max(), int((v == 0).sum())))

plt.figure(figsize=(9, 1.4))
plt.imshow(v.reshape(8, 64), cmap='Purples', aspect='auto')
plt.yticks([]); plt.title('사진 한 장이 만든 512칸'); plt.show()"""),

    Ex(1, "얼린 특징으로 판정 층을 학습시켜 **검증 정확도**를 `a` 에 담는다.\n"
          "> `train_head` 와 `acc` 는 준비 셀에 있다.",
       blank="head = train_head(___, ___)\na = acc(head, ___, ___)",
       answer="head = train_head(Xtr, Ytr)\na = acc(head, Xva, Yva)",
       check="print(round(a, 4))\nassert a > 0.9, f'0.9 는 넘어야 한다: {a}'"),

    Ex(2, "**종류별 정확도**를 따로 재서 `per` 에 담는다. `[개미, 벌]` 순서다.\n"
          "> 정답이 `c` 인 것 중 맞힌 비율이다.",
       setup="pred = head(Xva).argmax(1)",
       blank="per = [((pred == c) & (Yva == c)).sum().item() / (Yva == ___).sum().item()\n"
             "       for c in range(2)]",
       answer="per = [((pred == c) & (Yva == c)).sum().item() / (Yva == c).sum().item()\n"
              "       for c in range(2)]",
       check="print([round(x, 4) for x in per])\n"
             "assert len(per) == 2 and all(0 <= x <= 1 for x in per)"),

    Task(1, "사진을 **줄여** 가며 검증 정확도가 어떻게 되는지 적는다.\n"
            "> 각 종류에서 앞 `n // 2` 장씩만 골라 학습시킨다. 30 · 60 · 120 을 재 본다.",
         answer="""for n in (30, 60, 120):
    idx = torch.cat([torch.nonzero(Ytr == c).flatten()[: n // 2] for c in (0, 1)])
    h = train_head(Xtr[idx], Ytr[idx])
    print('%3d장 → %.4f' % (n, acc(h, Xva, Yva)))""",
         check="print('장수가 줄면 정확도도 준다')"),

    md("## 2. Threshold 를 움직여 본다"),
    md("모델이 내놓는 것은 판정이 아니라 **확률**이다. "
       "어디서 자를지는 사람이 정한다."),
    code("""with torch.no_grad():
    prob = torch.softmax(head(Xva), 1)[:, 1]      # 벌일 확률

for t in (0.2, 0.35, 0.5, 0.65, 0.8):
    p = (prob > t).long()
    a = ((p == 0) & (Yva == 0)).sum().item() / (Yva == 0).sum().item()
    b = ((p == 1) & (Yva == 1)).sum().item() / (Yva == 1).sum().item()
    print('Threshold %.2f  개미 %.3f  벌 %.3f  전체 %.4f'
          % (t, a, b, (p == Yva).float().mean()))"""),

    Ex(3, "Threshold 를 **0.8** 로 올렸을 때의 전체 정확도를 `a80` 에 담는다.",
       blank="a80 = ((prob > ___).long() == Yva).float().mean().item()",
       answer="a80 = ((prob > 0.8).long() == Yva).float().mean().item()",
       check="print(round(a80, 4))\nassert 0 < a80 <= 1"),

    Task(2, "Threshold 를 **0.05 부터 0.95 까지** 옮기며 개미 정확도와 벌 정확도를 그래프로 그린다.\n"
            "> 한쪽이 오르면 다른 쪽이 내려가는 것이 보여야 한다.",
         answer="""ts = [i / 20 for i in range(1, 20)]
A = [((((prob > t).long() == 0) & (Yva == 0)).sum() / (Yva == 0).sum()).item() for t in ts]
B = [((((prob > t).long() == 1) & (Yva == 1)).sum() / (Yva == 1).sum()).item() for t in ts]
plt.plot(ts, A, label='ants'); plt.plot(ts, B, label='bees')
plt.xlabel('Threshold'); plt.legend(); plt.grid(alpha=.3); plt.show()""",
         check="print('한쪽을 올리면 다른 쪽이 내려간다')"),

    md("## 3. 무엇이 어디에 있는가 — 객체탐지"),
    prep(YOLO_PREP),
    md("학습 없이 그대로 써 본다. 박스 하나가 **이름 · 신뢰도 · 네 숫자**다."),
    code("""r = det('bus.jpg')[0]
for b in r.boxes:
    print('%-8s %.3f  %s' % (det.names[int(b.cls)], float(b.conf),
                             [round(v) for v in b.xyxy[0].tolist()]))

plt.figure(figsize=(5, 7))
plt.imshow(r.plot()[:, :, ::-1]); plt.axis('off'); plt.show()"""),

    Ex(4, "신뢰도 Threshold 를 **0.05** 로 내렸을 때 박스가 몇 개인지 `n05` 에 담는다.",
       blank="n05 = len(det('bus.jpg', conf=___)[0].boxes)",
       answer="n05 = len(det('bus.jpg', conf=0.05)[0].boxes)",
       check="print(n05)\nassert n05 > len(det('bus.jpg', conf=0.25)[0].boxes)"),

    Task(3, "개미 사진 몇 장을 YOLO 에 넣어 **뭐라고 부르는지** 세어 본다.\n"
            "> COCO 80종에 `ant` 가 없다. 없는 이름은 답할 수 없다.",
         answer="""hit = {}
for p in sorted(glob.glob('hymenoptera_data/val/ants/*'))[:20]:
    for b in det(p, verbose=False)[0].boxes:
        k = det.names[int(b.cls)]
        hit[k] = hit.get(k, 0) + 1
print(sorted(hit.items(), key=lambda kv: -kv[1])[:5])
print('ant 가 COCO 에 있나 →', 'ant' in det.names.values())""",
         check="print('없는 이름은 답할 수 없다')"),

    md("## 4. 없는 이름을 가르친다 — 파인튜닝"),
    md("서명 데이터로 파인튜닝한다. 받아 온 그대로는 서명을 **하나도 못 찾는다**."),
    code("""ft = YOLO('yolo11n.pt')
ft.train(data='signature.yaml', epochs=15, imgsz=320, device=device, plots=False)
m = ft.val(data='signature.yaml')
print('mAP50 %.4f · 정밀도 %.4f · 재현율 %.4f'
      % (m.box.map50, m.box.mp, m.box.mr))
print('아는 종류', ft.names)"""),

    Ex(5, "파인튜닝한 모델로 서명 사진 한 장을 보고 **찾은 박스 수**를 `nb` 에 담는다.",
       setup="p = sorted(glob.glob('datasets/signature/images/val/*'))[0]",
       blank="nb = len(ft(p, conf=___)[0].boxes)",
       answer="nb = len(ft(p, conf=0.4)[0].boxes)",
       check="print(nb)\nassert isinstance(nb, int)"),

    Task(4, "**같은 사진**에 받아 온 모델과 파인튜닝한 모델을 각각 넣어 나란히 그린다.\n"
            "> 왼쪽은 아무것도 못 찾고 오른쪽은 서명을 찾는 것이 보여야 한다.",
         answer="""fig, ax = plt.subplots(1, 2, figsize=(11, 5))
ax[0].imshow(det(p, verbose=False)[0].plot()[:, :, ::-1]); ax[0].set_title('before'); ax[0].axis('off')
ax[1].imshow(ft(p, conf=0.4, verbose=False)[0].plot()[:, :, ::-1]); ax[1].set_title('after'); ax[1].axis('off')
plt.show()""",
         check="print('바뀐 것은 계수뿐이다')"),

    md("## 5. 영상에서 같은 것을 이어 본다 — 추적"),
    md("탐지만 하면 프레임마다 박스를 새로 센다. **몇 명이 지나갔는지**는 답하지 못한다."),
    code("""if not os.path.isfile('people.mp4'):
    os.system('wget -q https://media.roboflow.com/supervision/video-examples/'
              'people-walking.mp4 -O people.mp4')

import cv2
cap = cv2.VideoCapture('people.mp4')
boxes = 0
for _ in range(120):
    ok, fr = cap.read()
    if not ok: break
    boxes += len(det(fr, classes=[0], conf=0.35, verbose=False)[0].boxes)
cap.release()
print('탐지만 120프레임 → 박스 %d개. 그런데 몇 명인지는 모른다' % boxes)"""),

    md("`track` 으로 바꾸면 같은 사람에게 **같은 번호**가 붙는다."),
    code("""cap = cv2.VideoCapture('people.mp4')
ids = {}
for _ in range(120):
    ok, fr = cap.read()
    if not ok: break
    r = det.track(fr, classes=[0], conf=0.35, persist=True, verbose=False)[0]
    if r.boxes.id is not None:
        for i in r.boxes.id.int().tolist():
            ids[i] = ids.get(i, 0) + 1
cap.release()
print('붙은 번호 %d개' % len(ids))
print('1초(25프레임) 이상 유지된 번호 %d개' % sum(1 for v in ids.values() if v >= 25))"""),

    Ex(6, "**2초 이상** 머문 사람이 몇 명인지 `long2` 에 담는다.\n"
          "> 25fps 이므로 2초는 50프레임이다.",
       blank="long2 = sum(1 for v in ids.values() if v >= ___)",
       answer="long2 = sum(1 for v in ids.values() if v >= 50)",
       check="print(long2)\nassert long2 <= len(ids)"),

    Task(5, "가장 오래 머문 사람의 **체류 시간**을 초로 계산해 찍는다.",
         answer="""top = max(ids.values())
print('%d프레임 · %.1f초' % (top, top / 25))""",
         check="print('계수와 체류 시간이 추적으로 나온다')"),

    Task(6, "**조별로.** 추적 결과를 그대로 세면 인원이 부풀려진다. 왜 그런지 확인하고,\n"
            "짧게 끊긴 번호를 걸러 실제 인원에 가깝게 만들어 본다.\n"
            "> 번호별 유지 프레임 수를 히스토그램으로 그려 보면 보인다.",
         answer="""plt.hist(list(ids.values()), bins=20)
plt.xlabel('유지된 프레임 수'); plt.ylabel('번호 개수'); plt.show()
for k in (5, 15, 25, 50):
    print('%2d프레임 이상만 세면 → %d명' % (k, sum(1 for v in ids.values() if v >= k)))""",
         check="print('사람이 겹쳐 지나갈 때 번호가 바뀐다')"),
]

MODES = {
    ("ex", 1): "together", ("ex", 2): "together", ("task", 1): "solo",
    ("task", 2): "solo",
    ("ex", 3): "together", ("ex", 4): "together", ("task", 3): "solo",
    ("ex", 5): "together", ("task", 4): "solo",
    ("ex", 6): "together", ("task", 5): "solo", ("task", 6): "team",
}

SPEC = ("내 데이터로 분류기", "분류에서 탐지까지 · 남의 가중치를 받아 내 것으로", CELLS, MODES)
