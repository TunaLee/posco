"""2주차 D2 — 이미지 처리 · 객체탐지 · 파인튜닝 · 추적"""
from nbkit import md, code, h, lab, prep, Ex, Task

CELLS = [
    md("## 1. 사진을 512칸으로 바꾼다"),
    md("### 준비\n\n아래 준비 셀들을 **위에서부터 차례로** 한 번씩 실행한다.\n"
       "런타임을 **T4 GPU** 로 바꾼 뒤에 실행해야 뒤가 빠르다."),

    prep("""# 1) 오늘 쓸 것들을 불러온다
import os, sys, time, glob
import torch, torch.nn as nn
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms"""),

    prep("""# 2) GPU 가 켜졌는지 확인한다 — cpu 가 나오면 런타임을 T4 로 바꾼다
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print('장치', device)
if device == 'cuda':
    print(torch.cuda.get_device_name(0))"""),

    prep("""# 3) 사진을 내려받는다 — 폴더가 이미 있으면 건너뛴다
DRIVE_ZIP = ''      # 강사가 알려 주는 파일 ID 를 넣으면 드라이브에서 받는다
if not os.path.isdir('hymenoptera_data'):
    if DRIVE_ZIP:
        os.system(f'{sys.executable} -m pip install -q gdown')
        os.system(f'gdown {DRIVE_ZIP} -O hym.zip -q')
    if not os.path.isfile('hym.zip'):
        os.system('wget -q https://download.pytorch.org/tutorial/hymenoptera_data.zip -O hym.zip')
    os.system('unzip -q hym.zip')
print(sorted(os.listdir('hymenoptera_data')))"""),

    prep("""# 4) 크기를 맞추고 색 범위를 맞춘다 — 모델이 배울 때 쓰던 그 규칙이다
NORM = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
T = transforms.Compose([transforms.Resize(256), transforms.CenterCrop(224),
                        transforms.ToTensor(), NORM])"""),

    prep("""# 5) 폴더 이름이 그대로 라벨이 된다
train = datasets.ImageFolder('hymenoptera_data/train', T)
val   = datasets.ImageFolder('hymenoptera_data/val', T)
print(train.classes, '· 훈련', len(train), '장 · 검증', len(val), '장')"""),

    prep("""# 6) resnet18 을 받아 판정 층을 떼어 낸다 — 특징만 뽑는 몸통으로 쓴다
net = models.resnet18(weights='DEFAULT')
net.fc = nn.Identity()          # 마지막 층을 통과만 시킨다
net.eval().to(device)
print('판정 층 자리', net.fc)"""),

    prep("""# 7) 사진 한 장을 512칸으로 바꾸는 함수
def feats(ds):
    X, Y = [], []
    with torch.no_grad():                      # 배우지 않는다 — 계산만 한다
        for xb, yb in DataLoader(ds, batch_size=32):
            X.append(net(xb.to(device)).cpu()); Y.append(yb)
    return torch.cat(X), torch.cat(Y)"""),

    prep("""# 8) 397장을 전부 512칸으로 바꿔 둔다 — 한 번만 하면 된다
t0 = time.time()
Xtr, Ytr = feats(train)
Xva, Yva = feats(val)
print('%.1f초 · 훈련 %s · 검증 %s' % (time.time() - t0, tuple(Xtr.shape), tuple(Xva.shape)))"""),

    prep("""# 9) 512칸을 받아 둘 중 하나를 고르는 층을 학습시키는 함수
def train_head(X, Y, epochs=30, seed=42):
    torch.manual_seed(seed)                    # 고정해 둬야 매번 같은 결과가 나온다
    head = nn.Linear(512, 2)
    opt = torch.optim.Adam(head.parameters(), lr=0.001)
    loss_fn = nn.CrossEntropyLoss()
    for e in range(epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 32):
            b = perm[i:i + 32]
            opt.zero_grad(); loss_fn(head(X[b]), Y[b]).backward(); opt.step()
    return head"""),

    prep("""# 10) 맞힌 비율을 재는 함수
def acc(head, X, Y):
    with torch.no_grad():
        return (head(X).argmax(1) == Y).float().mean().item()"""),

    md("사진 한 장이 512칸이 된 것을 직접 본다."),
    code("""# 첫 장의 512칸 중 앞 12개만 찍어 본다
v = Xtr[0]
print([round(float(x), 2) for x in v[:12]])
print('최소 %.2f · 최대 %.2f · 0 인 칸 %d개' % (v.min(), v.max(), int((v == 0).sum())))"""),

    code("""# 512칸을 8×64 로 접어 그림으로 본다 — 진한 칸이 강하게 반응한 특징이다
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

    prep("""# 판정 층을 하나 만들어 둔다 — seed 가 고정이라 늘 같은 결과다
head = train_head(Xtr, Ytr)
print('검증 정확도 %.4f' % acc(head, Xva, Yva))"""),

    prep("""# 검증 사진마다 <벌일 확률> 을 뽑아 둔다
with torch.no_grad():
    prob = torch.softmax(head(Xva), 1)[:, 1]
print('앞 8장의 확률', [round(float(x), 3) for x in prob[:8]])"""),

    code("""# 자르는 자리를 옮겨 가며 무엇이 오르고 무엇이 내리는지 본다
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

    prep("""# 1) 탐지 라이브러리를 깐다 — 한 번만 하면 된다
os.system(f'{sys.executable} -m pip install -q ultralytics')
from ultralytics import YOLO"""),

    prep("""# 2) 시험용 사진 한 장을 받는다
if not os.path.isfile('bus.jpg'):
    os.system('wget -q https://ultralytics.com/images/bus.jpg')
print(os.path.isfile('bus.jpg'))"""),

    prep("""# 3) 오픈 가중치를 받아 온다 — 파일이 없으면 알아서 내려받는다
det = YOLO('yolo11n.pt')
print('아는 종류', len(det.names), '개 · 계수',
      sum(p.numel() for p in det.model.parameters()))"""),

    md("학습 없이 그대로 써 본다. 박스 하나가 **이름 · 신뢰도 · 네 숫자**다."),
    code("""# 박스마다 무엇을 · 얼마나 확신하고 · 어디서 찾았는지 찍는다
r = det('bus.jpg')[0]
for b in r.boxes:
    print('%-8s %.3f  %s' % (det.names[int(b.cls)], float(b.conf),
                             [round(v) for v in b.xyxy[0].tolist()]))"""),

    code("""# 같은 결과를 그림으로 본다 — plot() 은 BGR 이라 뒤집어서 넘긴다
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
    md("가르치려면 **상자를 친 사진**이 있어야 한다. 상자는 Roboflow · Label Studio · CVAT · labelImg "
       "같은 도구에서 그리고, `YOLO` 형식으로 Export 하면 아래 폴더가 그대로 나온다.\n\n"
       "여기서는 이미 상자를 쳐 둔 **서명 데이터**를 받아 그 폴더를 열어 본다."),

    prep("""# 1) 자료를 받아 온다 — yaml 이름만 주면 폴더까지 내려받는다
from ultralytics.data.utils import check_det_dataset

info = check_det_dataset('signature.yaml')
root = str(info['path'])
print('폴더', root)
print('종류', info['names'])"""),

    code("""# 2) 라벨링 도구가 Export 해 주는 폴더 모양 그대로다
for d in ('images/train', 'labels/train', 'images/val', 'labels/val'):
    print('%-14s %3d개' % (d, len(glob.glob(os.path.join(root, d, '*')))))"""),

    md("사진 한 장과 **같은 이름의 글자 파일**이 짝을 이룬다. 그 한 줄이 상자 하나다."),
    code("""# 사진 하나를 골라 짝이 되는 라벨 파일을 연다
p = sorted(glob.glob(root + '/images/train/*'))[0]
t = p.replace('/images/', '/labels/').rsplit('.', 1)[0] + '.txt'
print('사진', os.path.basename(p))
print('라벨', open(t).read().strip())"""),

    md("글자 다섯 개를 **다시 상자로 되돌려** 본다. 사람이 도구에서 그린 그 상자다."),
    code("""# 종류번호 · 중심x · 중심y · 너비 · 높이 — 뒤 넷은 0 과 1 사이 값이다
im = plt.imread(p)
H, W = im.shape[:2]
c, cx, cy, w, h = map(float, open(t).read().split()[:5])
print('사진 %d×%d · 상자 중심 (%.0f, %.0f)' % (W, H, cx * W, cy * H))"""),

    code("""# 0~1 값에 사진 크기를 곱하면 픽셀 자리가 나온다
plt.figure(figsize=(6, 4))
plt.imshow(im)
plt.gca().add_patch(plt.Rectangle(((cx - w / 2) * W, (cy - h / 2) * H),
                                  w * W, h * H, fill=False, color='#E8537A', lw=2))
plt.axis('off'); plt.title(info['names'][int(c)]); plt.show()"""),

    Ex(7, "상자가 **사진 넓이의 몇 %** 를 차지하는지 `frac` 에 담는다.\n"
          "> 너비와 높이는 이미 0 과 1 사이 값이다.",
       blank="frac = ___ * ___ * 100",
       answer="frac = w * h * 100",
       check="print('%.1f%%' % frac)\nassert 0 < frac < 100"),

    Task(7, "`images` 와 `labels` 의 **짝이 맞는지** 확인한다.\n"
            "> 짝이 없는 사진은 배경으로 학습된다. 학습은 도는데 성능이 안 오르면 여기를 본다.",
         answer="""def stems(d):
    return {os.path.splitext(os.path.basename(x))[0] for x in glob.glob(root + '/' + d + '/*')}

for split in ('train', 'val'):
    a, b = stems('images/' + split), stems('labels/' + split)
    print(split, '· 라벨 없는 사진', len(a - b), '· 사진 없는 라벨', len(b - a))""",
         check="print('이름이 같아야 짝이 된다')"),

    md("서명 데이터로 파인튜닝한다. 받아 온 그대로는 서명을 **하나도 못 찾는다**."),

    prep("""# 1) 받아 온 계수에서 출발해 서명 쪽으로 옮긴다 — 몇 분 걸린다
ft = YOLO('yolo11n.pt')
ft.train(data='signature.yaml', epochs=15, imgsz=320, device=device, plots=False)"""),

    prep("""# 2) 검증 폴더로 채점한다
m = ft.val(data='signature.yaml')
print('mAP50 %.4f · 정밀도 %.4f · 재현율 %.4f'
      % (m.box.map50, m.box.mp, m.box.mr))
print('아는 종류', ft.names)"""),

    prep("""# 3) 견줘 볼 검증 사진 한 장을 골라 둔다
p = sorted(glob.glob(root + '/images/val/*'))[0]
print(os.path.basename(p))"""),

    Ex(5, "파인튜닝한 모델로 서명 사진 한 장을 보고 **찾은 박스 수**를 `nb` 에 담는다.",
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

    prep("""# 1) 사람이 지나가는 영상을 받는다
import cv2
if not os.path.isfile('people.mp4'):
    os.system('wget -q https://media.roboflow.com/supervision/video-examples/'
              'people-walking.mp4 -O people.mp4')
print(os.path.isfile('people.mp4'))"""),

    code("""# 2) 탐지만 해 본다 — 프레임마다 박스를 새로 센다
cap = cv2.VideoCapture('people.mp4')
boxes = 0
for _ in range(120):
    ok, fr = cap.read()
    if not ok: break
    boxes += len(det(fr, classes=[0], conf=0.35, verbose=False)[0].boxes)
cap.release()
print('120프레임에서 박스 %d개 — 그런데 몇 명인지는 모른다' % boxes)"""),

    md("`track` 으로 바꾸면 같은 사람에게 **같은 번호**가 붙는다."),
    prep("""# 3) track 으로 바꿔 번호별로 몇 프레임 머물렀는지 센다
cap = cv2.VideoCapture('people.mp4')
ids = {}
for _ in range(120):
    ok, fr = cap.read()
    if not ok: break
    r = det.track(fr, classes=[0], conf=0.35, persist=True, verbose=False)[0]
    if r.boxes.id is not None:
        for i in r.boxes.id.int().tolist():
            ids[i] = ids.get(i, 0) + 1
cap.release()
print('붙은 번호 %d개' % len(ids))"""),

    code("""# 4) 잠깐 스친 번호를 빼면 실제 인원에 가까워진다
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

    md("## 6. GPU 없이 — API 로 이미지 처리"),
    md("여기부터는 T4 가 필요 없다. 사진을 **NVIDIA 서버로 보내고 결과만 받는다**.\n\n"
       "**이 절은 위를 건너뛰고 여기서부터 실행해도 된다.** "
       "필요한 것을 아래 첫 두 셀에서 다시 갖춘다.\n\n"
       "[build.nvidia.com](https://build.nvidia.com) 에서 무료로 키를 받는다. "
       "키는 입력 칸에 **붙여 넣는다** — 코드에 적으면 노트북에 그대로 남는다."),

    code("""# 1) 이 절만 따로 돌려도 되게 — 쓰는 것을 여기서 다시 불러온다
import os, sys, io, glob, base64, getpass
import requests, torch
import matplotlib.pyplot as plt
from PIL import Image

print('준비됨 ·', sys.version.split()[0])"""),

    code("""# 2) 사진 두 벌을 갖춘다 — 이미 있으면 건너뛴다
if not os.path.isfile('bus.jpg'):
    os.system('wget -q https://ultralytics.com/images/bus.jpg')
if not os.path.isdir('hymenoptera_data'):
    os.system('wget -q https://download.pytorch.org/tutorial/hymenoptera_data.zip -O hym.zip')
    os.system('unzip -q hym.zip')
print('bus.jpg', os.path.isfile('bus.jpg'), '· 개미벌 폴더', os.path.isdir('hymenoptera_data'))"""),

    code("""# 3) 키를 받아 둔다 — 화면에 찍히지 않는다
API_KEY = os.environ.get('NVIDIA_API_KEY') or getpass.getpass('NVIDIA API 키: ')
HDR = {'Authorization': 'Bearer ' + API_KEY, 'Accept': 'application/json'}
print('키를 받았다 · 길이', len(API_KEY))"""),

    code("""# 4) 지금 살아 있는 모델을 먼저 확인한다 — 목록은 자주 바뀐다
r = requests.get('https://integrate.api.nvidia.com/v1/models', headers=HDR, timeout=30)
ids = [m['id'] for m in r.json()['data']] if r.status_code == 200 else []
print('쓸 수 있는 모델', len(ids), '개')
print([i for i in ids if any(k in i for k in ('vl', 'vision', 'multimodal', 'clip'))][:12])"""),

    code("""# 5) CV 엔드포인트가 살아 있는지 본다 — 키 없이도 확인된다
CV = 'https://ai.api.nvidia.com/v1/cv/'
MEAN = {401: '살아 있다', 410: '내려갔다', 404: '없는 주소다'}
for name in ('nvidia/nv-grounding-dino', 'nvidia/nemotron-ocr-v2', 'nvidia/ocdrnet'):
    c = requests.post(CV + name, json={}, timeout=20).status_code
    print('%-26s %s  %s' % (name, c, MEAN.get(c, '?')))"""),

    code("""# 6) 사진을 연다 — 파일 경로와 http 주소를 둘 다 받는다
def load_image(src):
    if src.startswith('http'):
        r = requests.get(src, timeout=30)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert('RGB')
    return Image.open(src).convert('RGB')"""),

    code("""# 7) 주소로 한 장 · 파일로 한 장 열어 본다
IMG = 'https://ultralytics.com/images/bus.jpg'      # 내 사진 주소로 바꿔도 된다
im = load_image(IMG)
print('주소에서', im.size, '·', '파일에서', load_image('bus.jpg').size)"""),

    code("""# 8) 사진을 글자로 바꾼다 — 200KB 를 넘으면 서버가 안 받는다
def to_uri(im, side=640, quality=85):
    im = im.copy()
    im.thumbnail((side, side))                      # 긴 변을 side 에 맞춘다
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=quality)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

print('%.0fKB' % (len(to_uri(im)) * 3 / 4 / 1024))"""),

    md("### 말로 지정하는 객체 탐지 — Grounding DINO\n\n"
       "YOLO 는 COCO 80종만 알았다. 이 모델은 **찾을 것을 글자로 적어 보낸다**."),

    code("""# 9) 찾을 것을 글자로 적어 보내는 함수
GDINO = 'https://ai.api.nvidia.com/v1/cv/nvidia/nv-grounding-dino'

def find(src, phrases, threshold=0.3):
    im = load_image(src)
    body = {'model': 'Grounding-Dino', 'threshold': threshold,
            'messages': [{'role': 'user', 'content': [
                {'type': 'text', 'text': phrases},
                {'type': 'media_url', 'media_url': {'url': to_uri(im)}}]}]}
    r = requests.post(GDINO, headers=HDR, json=body, timeout=60)
    if r.status_code != 200:
        print(r.status_code, r.text[:300])          # 무엇이 틀렸는지 그대로 본다
    r.raise_for_status()
    return im, r.json()['choices'][0]['message']['content']"""),

    code("""# 10) COCO 에 없는 이름도 넣어 본다
im, out = find(IMG, 'person, bus, backpack, license plate')
for g in out['boundingBoxes']:
    print('%-14s %d개  %s' % (g['phrase'], len(g['bboxes']),
                              [round(c, 2) for c in g['confidence']]))"""),

    code("""# 11) 돌아온 네 숫자를 그리는 함수 — day6 에서 쓰던 그 박스다
def draw(im, out, title=''):
    plt.figure(figsize=(5, 6)); plt.imshow(im); ax = plt.gca()
    sx, sy = im.width / out['frameWidth'], im.height / out['frameHeight']
    for g in out['boundingBoxes']:
        for (x1, y1, x2, y2), c in zip(g['bboxes'], g['confidence']):
            ax.add_patch(plt.Rectangle((x1 * sx, y1 * sy), (x2 - x1) * sx, (y2 - y1) * sy,
                                       fill=False, color='#5B3DF5', lw=2))
            ax.text(x1 * sx, y1 * sy - 5, '%s %.2f' % (g['phrase'], c), fontsize=8, color='#5B3DF5')
    plt.axis('off'); plt.title(title); plt.show()"""),

    code("""# 12) 그려 본다 — 문장에 적은 것만 박스가 된다
draw(im, out, 'person, bus, backpack, license plate')"""),

    Ex(8, "COCO 에 없던 `ant` 를 찾게 해서 박스 수를 `n_ant` 에 담는다.\n"
          "> day6 앞에서 YOLO 는 개미를 한 마리도 못 찾았다.",
       setup="p_ant = sorted(glob.glob('hymenoptera_data/val/ants/*'))[0]",
       blank="im2, o = find(p_ant, ___)\n"
             "n_ant = sum(len(g['bboxes']) for g in o['boundingBoxes'])\n"
             "draw(im2, o, 'ant %d개' % n_ant)",
       answer="im2, o = find(p_ant, 'ant')\n"
              "n_ant = sum(len(g['bboxes']) for g in o['boundingBoxes'])\n"
              "draw(im2, o, 'ant %d개' % n_ant)",
       check="print(n_ant)\nassert isinstance(n_ant, int)"),

    md("### 학습 없이 분류 — NV-CLIP\n\n"
       "사진과 글을 **같은 자리에 놓는** 모델이다. 가까운 쪽이 답이 된다."),

    code("""# 13) 사진이든 글이든 벡터로 바꿔 주는 함수 — 한 번에 64개까지
CLIP = 'https://integrate.api.nvidia.com/v1/embeddings'

def embed(items):
    r = requests.post(CLIP, headers=HDR, timeout=60,
                      json={'model': 'nvidia/nvclip', 'input': items})
    if r.status_code != 200:
        print(r.status_code, r.text[:300])
    r.raise_for_status()
    return torch.tensor([d['embedding'] for d in r.json()['data']])"""),

    code("""# 14) 개미 4장 · 벌 4장과 설명 두 줄을 한꺼번에 보낸다
paths = (sorted(glob.glob('hymenoptera_data/val/ants/*'))[:4]
         + sorted(glob.glob('hymenoptera_data/val/bees/*'))[:4])
LAB = ['a photo of an ant', 'a photo of a bee']
V = embed([to_uri(load_image(p), 336) for p in paths] + LAB)
print('사진 8장 + 글 2줄 →', tuple(V.shape))"""),

    code("""# 15) 가까운 쪽을 고른다 — 학습은 한 줄도 하지 않았다
E = torch.nn.functional.normalize(V, dim=1)
sim = E[:8] @ E[8:].T
truth = torch.tensor([0] * 4 + [1] * 4)
print('맞은 개수 %d / 8' % int((sim.argmax(1) == truth).sum()))"""),

    code("""# 16) 사진마다 무엇이라 답했는지 그림으로 본다 — 파랑이 맞은 것이다
fig, ax = plt.subplots(2, 4, figsize=(11, 5.5))
for a, p, k, row in zip(ax.ravel(), paths, sim.argmax(1), sim):
    a.imshow(load_image(p)); a.axis('off')
    ok = int(k) == (0 if '/ants/' in p else 1)
    a.set_title('%s  %.3f' % (LAB[int(k)].split()[-1], row[int(k)]),
                color='#5B3DF5' if ok else '#E8537A', fontsize=11)
plt.tight_layout(); plt.show()"""),

    Ex(9, "설명을 `['ant', 'bee']` 로 줄여 다시 재고 맞은 개수를 `n_plain` 에 담는다.\n"
          "> 사진은 그대로다. 바뀐 것은 글뿐이다.",
       blank="V2 = embed([to_uri(load_image(p), 336) for p in paths] + ___)\n"
             "E2 = torch.nn.functional.normalize(V2, dim=1)\n"
             "n_plain = int(((E2[:8] @ E2[8:].T).argmax(1) == truth).sum())",
       answer="V2 = embed([to_uri(load_image(p), 336) for p in paths] + ['ant', 'bee'])\n"
              "E2 = torch.nn.functional.normalize(V2, dim=1)\n"
              "n_plain = int(((E2[:8] @ E2[8:].T).argmax(1) == truth).sum())",
       check="print(n_plain, '/ 8')\nassert 0 <= n_plain <= 8"),

    md("### 사진을 보고 말로 답한다 — VLM\n\n"
       "여기까지는 **후보를 내가 줬다**. YOLO 는 80개 목록, Grounding DINO 는 내 문장, "
       "NV-CLIP 은 내가 쓴 설명 두 줄이다.\n\n"
       "VLM 은 후보를 안 준다. 사진을 **토큰 몇백 개로 바꿔 문장 앞에 붙이고**, "
       "그다음부터는 **다음 낱말을 이어 쓴다**. 고를 후보가 낱말 전체라서 목록이 필요 없다."),

    code("""# 17) 위에서 받아 온 목록에 있는 것 중 첫 번째를 쓴다 — 이름은 계속 바뀐다
CAND = ['nvidia/nemotron-nano-12b-v2-vl',
        'nvidia/llama-3.1-nemotron-nano-vl-8b-v1',
        'meta/llama-3.2-11b-vision-instruct']
VLM_MODEL = next((m for m in CAND if m in ids), CAND[0])
print('쓸 모델', VLM_MODEL, '· 목록에 있나', VLM_MODEL in ids)"""),

    code("""# 18) 사진과 물음을 같이 보내는 함수
VLM = 'https://integrate.api.nvidia.com/v1/chat/completions'

def ask(src, question, max_tokens=300):
    im = load_image(src)
    b64 = to_uri(im).split(',', 1)[1]
    assert len(b64) < 180_000, '사진이 크다 — to_uri 의 side 를 줄인다'
    msg = question + ' <img src="data:image/jpeg;base64,' + b64 + '" />'
    r = requests.post(VLM, headers=HDR, timeout=90,
                      json={'model': VLM_MODEL, 'max_tokens': max_tokens,
                            'messages': [{'role': 'user', 'content': msg}]})
    if r.status_code != 200:
        print(r.status_code, r.text[:300])
    r.raise_for_status()
    return im, r.json()['choices'][0]['message']['content']"""),

    code("""# 19) 사진과 답을 같이 본다
im3, txt = ask(IMG, '이 사진에 무엇이 보이는지 한국어 두 문장으로 답하라.')
plt.figure(figsize=(4, 5.5)); plt.imshow(im3); plt.axis('off'); plt.show()
print(txt)"""),

    code("""# 20) 판정 기준을 글로 바꿔 넣는다 — 코드는 그대로다
_, ans = ask(IMG, '이 사진에 사람이 있으면 {"사람": true}, 없으면 {"사람": false} 로만 답하라.')
print(ans)"""),

    code("""# 21) 후보를 준 것과 안 준 것을 같은 사진으로 견준다
p_one = paths[0]
print('CLIP   후보 2개 중 →', LAB[int(sim[0].argmax())])
_, free = ask(p_one, '이 사진에 무엇이 있는지 한국어 한 문장으로 답하라.')
print('VLM    후보 없이  →', free.strip())"""),

    md("파인튜닝은 상자를 며칠 그려야 시작된다. API 는 **찾을 것을 한 줄 적으면 끝**이다.\n"
       "대신 현장에서만 쓰는 이름은 못 알아듣고, 사진이 밖으로 나간다. 둘은 바꿔 쓰는 관계다."),
]

MODES = {
    ("ex", 1): "together", ("ex", 2): "together", ("task", 1): "solo",
    ("task", 2): "solo",
    ("ex", 3): "together", ("ex", 4): "together", ("task", 3): "solo",
    ("ex", 5): "together", ("task", 4): "solo",
    ("ex", 7): "together", ("task", 7): "solo",
    ("ex", 6): "together", ("task", 5): "solo", ("task", 6): "team",
    ("ex", 8): "together", ("ex", 9): "together",
}

SPEC = ("이미지 처리", "분류에서 탐지까지 · 남의 가중치를 받아 내 것으로", CELLS, MODES)
