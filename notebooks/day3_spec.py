"""Day 3 — 머신러닝 실습 스펙"""
from nbkit import md, code, h, lab, Ex, Task

URL = "https://tunalee.github.io/posco/data/batch_quality.csv"

# 전처리는 Day 2 에서 만든 순서를 함수 하나로 굳혀 두고 계속 쓴다.
PREP = f"""import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def load():
    df = pd.read_csv('{URL}', thousands=',', na_values=['N/A', '-'])
    df['설비호기'] = df['설비호기'].str.strip().str.upper()
    df['입도'] = df['입도'].fillna(df['입도'].median())
    df = df.dropna(subset=['수분율'])
    return pd.get_dummies(df, columns=['설비호기', '교대조'], drop_first=True)

def split(target='양품여부'):
    d = load()
    drop = ['양품여부', '방전용량', '배치번호']
    X, y = d.drop(columns=drop), d[target]
    return train_test_split(X, y, test_size=0.2, random_state=42,
                            stratify=y if target == '양품여부' else None)"""

CELLS = [
    # ══════════════════════════════════════════════════════════════════
    h(2, "1. 학습의 원리"),

    lab("경사 하강법은 기울기의 반대로 조금씩 내려간다. 손으로 한 번 굴려 본다."),
    code("""
def f(x):      return (x - 3) ** 2 + 1     # 최솟값은 x = 3
def grad(x):   return 2 * (x - 3)

x, lr = 10.0, 0.1
for step in range(1, 21):
    x = x - lr * grad(x)
    if step % 5 == 0:
        print(f"{step:>3}회  x={x:6.3f}  f(x)={f(x):6.3f}")
"""),

    Ex(1, "학습률을 `0.01` 로 낮추고 같은 20회를 돌린 뒤 `x` 를 확인한다.\n"
          "값이 3에 **덜 가까워지는 것**을 본다.",
       setup="def grad(x): return 2 * (x - 3)\nx = 10.0",
       blank="lr = ___\nfor _ in range(20):\n    x = x - lr * grad(x)",
       answer="lr = 0.01\nfor _ in range(20):\n    x = x - lr * grad(x)",
       check="assert x > 4, f'학습률이 작으면 20회로는 못 간다. 실제 {x}'\nprint('통과 — x =', round(x, 3))"),

    Ex(2, "학습률을 `1.1` 로 올리면 어떻게 되는지 본다. `x` 가 **발산**한다.",
       setup="def grad(x): return 2 * (x - 3)\nx = 10.0",
       blank="lr = ___\nfor _ in range(20):\n    x = x - lr * grad(x)",
       answer="lr = 1.1\nfor _ in range(20):\n    x = x - lr * grad(x)",
       check="assert abs(x) > 100, f'학습률이 너무 크면 튕겨 나간다. 실제 {x}'\nprint('통과 — x =', round(x, 1))"),

    lab("손실 함수는 예측이 얼마나 틀렸는지를 숫자 하나로 만든다."),
    code("""
import numpy as np

y_true = np.array([170.0, 175.0, 168.0, 180.0])
y_pred = np.array([172.0, 174.0, 165.0, 179.0])

mse = ((y_true - y_pred) ** 2).mean()
mae = np.abs(y_true - y_pred).mean()
print('MSE', round(mse, 3), ' MAE', round(mae, 3))

# 이상치를 하나 섞으면 MSE 만 크게 뛴다
y_pred2 = y_pred.copy(); y_pred2[0] = 120.0
print('이상치 후 MSE', round(((y_true - y_pred2) ** 2).mean(), 1),
      ' MAE', round(np.abs(y_true - y_pred2).mean(), 1))
"""),

    h(2, "2. scikit-learn — 네 줄로 끝나는 학습"),

    lab("어떤 모델이든 만들고·학습하고·예측하고·점수 보는 네 줄이다."),
    code(f"""
{PREP}

from sklearn.linear_model import LogisticRegression

X_tr, X_te, y_tr, y_te = split()
sc = StandardScaler()
X_tr_s, X_te_s = sc.fit_transform(X_tr), sc.transform(X_te)

model = LogisticRegression(max_iter=1000)   # 만들고
model.fit(X_tr_s, y_tr)                     # 학습하고
pred = model.predict(X_te_s)                # 예측하고
print(round(model.score(X_te_s, y_te), 3))  # 점수 본다
"""),

    lab("계수를 보면 어떤 열이 답을 밀고 당기는지 드러난다."),
    code(f"""
{PREP}
from sklearn.linear_model import LogisticRegression

X_tr, X_te, y_tr, y_te = split()
sc = StandardScaler()
model = LogisticRegression(max_iter=1000).fit(sc.fit_transform(X_tr), y_tr)

coef = dict(zip(X_tr.columns, model.coef_[0].round(2)))
for k, v in sorted(coef.items(), key=lambda kv: -abs(kv[1]))[:5]:
    print(f"{{k:>16}}  {{v:+.2f}}")
"""),

    Ex(4, "로지스틱 회귀를 학습하고 **테스트 정확도**를 `acc` 에 담는다.",
       setup=PREP + "\nfrom sklearn.linear_model import LogisticRegression\n"
                    "X_tr, X_te, y_tr, y_te = split()\n"
                    "sc = StandardScaler()\n"
                    "X_tr_s, X_te_s = sc.fit_transform(X_tr), sc.transform(X_te)",
       blank="model = ___\nmodel.fit(X_tr_s, y_tr)\nacc = ___",
       answer="model = LogisticRegression(max_iter=1000)\nmodel.fit(X_tr_s, y_tr)\n"
              "acc = model.score(X_te_s, y_te)",
       check="assert acc > 0.85, f'0.85 는 넘어야 한다. 실제 {acc}'\nprint('통과 — 정확도', round(acc, 3))"),

    Ex(5, "결정 트리를 `max_depth=3` 으로 학습하고 정확도를 `acc` 에 담는다.\n"
          "> 트리는 스케일링이 필요 없다. 원본 `X_tr` 을 그대로 넣는다.",
       setup=PREP + "\nfrom sklearn.tree import DecisionTreeClassifier\n"
                    "X_tr, X_te, y_tr, y_te = split()",
       blank="model = ___\nmodel.fit(X_tr, y_tr)\nacc = ___",
       answer="model = DecisionTreeClassifier(max_depth=3, random_state=42)\n"
              "model.fit(X_tr, y_tr)\nacc = model.score(X_te, y_te)",
       check="assert acc > 0.88, f'실제 {acc}'\nprint('통과 — 정확도', round(acc, 3))"),

    lab("트리가 무엇을 보고 갈랐는지 글로 뽑아 볼 수 있다."),
    code(f"""
{PREP}
from sklearn.tree import DecisionTreeClassifier, export_text

X_tr, X_te, y_tr, y_te = split()
tree = DecisionTreeClassifier(max_depth=2, random_state=42).fit(X_tr, y_tr)
print(export_text(tree, feature_names=list(X_tr.columns)))
"""),

    Ex(6, "랜덤 포레스트를 학습하고 **중요도가 가장 높은 열**의 이름을 `top` 에 담는다.",
       setup=PREP + "\nfrom sklearn.ensemble import RandomForestClassifier\n"
                    "X_tr, X_te, y_tr, y_te = split()",
       blank="model = ___\nmodel.fit(X_tr, y_tr)\ntop = ___",
       answer="model = RandomForestClassifier(n_estimators=200, random_state=42)\n"
              "model.fit(X_tr, y_tr)\n"
              "pairs = sorted(zip(model.feature_importances_, X_tr.columns), reverse=True)\n"
              "top = pairs[0][1]",
       check="assert top == '소성온도', f'기대 소성온도, 실제 {top}'\nprint('통과')"),

    Task(1, "세 모델(로지스틱·결정 트리·랜덤 포레스트)의 테스트 정확도를 재어\n"
            "`scores` 딕셔너리에 담고 출력한다.\n"
            "> 로지스틱만 스케일링한 데이터를 쓴다.",
         setup=PREP + "\nfrom sklearn.linear_model import LogisticRegression\n"
                      "from sklearn.tree import DecisionTreeClassifier\n"
                      "from sklearn.ensemble import RandomForestClassifier\n"
                      "X_tr, X_te, y_tr, y_te = split()",
         answer="sc = StandardScaler()\n"
                "X_tr_s, X_te_s = sc.fit_transform(X_tr), sc.transform(X_te)\n"
                "scores = {}\n"
                "scores['logistic'] = LogisticRegression(max_iter=1000).fit(X_tr_s, y_tr).score(X_te_s, y_te)\n"
                "scores['tree'] = DecisionTreeClassifier(max_depth=3, random_state=42).fit(X_tr, y_tr).score(X_te, y_te)\n"
                "scores['forest'] = RandomForestClassifier(n_estimators=200, random_state=42).fit(X_tr, y_tr).score(X_te, y_te)\n"
                "for k, v in scores.items():\n"
                "    print(f'{k:>10} {v:.3f}')",
         check="assert set(scores) == {'logistic', 'tree', 'forest'}, f'키 확인: {scores.keys()}'\n"
               "assert scores['forest'] > scores['logistic'], '포레스트가 로지스틱보다 낫다'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "3. 검증과 평가"),

    lab("정확도만 보면 속는다. 전부 양품이라 찍어도 81% 가 나온다."),
    code(f"""
{PREP}

X_tr, X_te, y_tr, y_te = split()
print('테스트셋 양품 비율:', round(y_te.mean(), 3))
print('전부 1이라 찍은 정확도:', round((y_te == 1).mean(), 3))
"""),

    Ex(7, "**전부 양품이라 찍는** 예측을 만들어 정확도를 `dumb_acc` 에 담는다.",
       setup=PREP + "\nimport numpy as np\nX_tr, X_te, y_tr, y_te = split()",
       blank="pred = ___\ndumb_acc = ___",
       answer="pred = np.ones(len(y_te), dtype=int)\ndumb_acc = (pred == y_te).mean()",
       check="assert abs(dumb_acc - 0.81) < 0.02, f'실제 {dumb_acc}'\n"
             "print('통과 — 아무것도 안 배워도', round(dumb_acc, 3))"),

    lab("혼동 행렬은 어디서 틀렸는지 네 칸으로 보여 준다."),
    code(f"""
{PREP}
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report

X_tr, X_te, y_tr, y_te = split()
model = RandomForestClassifier(n_estimators=200, random_state=42).fit(X_tr, y_tr)
pred = model.predict(X_te)

print(confusion_matrix(y_te, pred))
print(classification_report(y_te, pred, target_names=['불량', '양품']))
"""),

    Ex(8, "불량(`0`)을 **놓친 건수**를 `missed` 에 담는다.\n"
          "> 실제 불량인데 양품이라 예측한 것이다. 혼동 행렬의 어느 칸인지 생각한다.",
       setup=PREP + "\nfrom sklearn.ensemble import RandomForestClassifier\n"
                    "from sklearn.metrics import confusion_matrix\n"
                    "X_tr, X_te, y_tr, y_te = split()\n"
                    "model = RandomForestClassifier(n_estimators=200, random_state=42).fit(X_tr, y_tr)\n"
                    "pred = model.predict(X_te)\ncm = confusion_matrix(y_te, pred)",
       blank="missed = ___",
       answer="missed = cm[0, 1]",
       check="assert missed == ((y_te == 0) & (pred == 1)).sum(), f'실제 놓친 수와 다르다: {missed}'\n"
             "print('통과 — 놓친 불량', missed, '건')"),

    Ex(9, "불량을 양성으로 놓고 **재현율**을 구해 `recall` 에 담는다.\n"
          "> `recall_score(..., pos_label=0)` 이다.",
       setup=PREP + "\nfrom sklearn.ensemble import RandomForestClassifier\n"
                    "from sklearn.metrics import recall_score\n"
                    "X_tr, X_te, y_tr, y_te = split()\n"
                    "model = RandomForestClassifier(n_estimators=200, random_state=42).fit(X_tr, y_tr)\n"
                    "pred = model.predict(X_te)",
       blank="recall = ___",
       answer="recall = recall_score(y_te, pred, pos_label=0)",
       check="assert 0.6 < recall < 1.0, f'실제 {recall}'\nprint('통과 — 재현율', round(recall, 3))"),


    Task(3, "**과적합**을 눈으로 본다. 결정 트리의 `max_depth` 를 1부터 20까지 늘리며\n"
            "훈련 정확도와 테스트 정확도를 같이 재어 그린다.\n"
            "> 훈련은 계속 오르는데 테스트는 어느 지점부터 안 오른다.",
         setup=PREP + "\nfrom sklearn.tree import DecisionTreeClassifier\n"
                      "import matplotlib.pyplot as plt\n"
                      "X_tr, X_te, y_tr, y_te = split()",
         answer="depths = range(1, 21)\ntr, te = [], []\n"
                "for d_ in depths:\n"
                "    m = DecisionTreeClassifier(max_depth=d_, random_state=42).fit(X_tr, y_tr)\n"
                "    tr.append(m.score(X_tr, y_tr))\n"
                "    te.append(m.score(X_te, y_te))\n"
                "plt.plot(depths, tr, label='train')\n"
                "plt.plot(depths, te, label='test')\n"
                "plt.xlabel('max_depth'); plt.ylabel('accuracy'); plt.legend(); plt.show()",
         check="assert tr[-1] > te[-1], '깊어질수록 훈련 점수가 테스트보다 높아진다'\n"
               "assert tr[-1] > 0.99, f'끝에서 훈련 정확도는 1에 가깝다: {tr[-1]}'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "4. 회귀 — 용량 맞히기"),

    lab("분류가 아니라 숫자를 맞힌다. 정답 열만 바꾸면 나머지는 같다."),
    code(f"""
{PREP}
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

X_tr, X_te, y_tr, y_te = split(target='방전용량')

lin = LinearRegression().fit(X_tr, y_tr)
rf = RandomForestRegressor(n_estimators=200, random_state=42).fit(X_tr, y_tr)

for name, m in (('linear', lin), ('forest', rf)):
    p = m.predict(X_te)
    print(f"{{name:>8}}  R2 {{r2_score(y_te, p):.3f}}  RMSE {{mean_squared_error(y_te, p) ** 0.5:.2f}}")
"""),

    Ex(10, "선형 회귀로 `방전용량` 을 예측하고 **R²** 를 `r2` 에 담는다.",
        setup=PREP + "\nfrom sklearn.linear_model import LinearRegression\n"
                     "from sklearn.metrics import r2_score\n"
                     "X_tr, X_te, y_tr, y_te = split(target='방전용량')",
        blank="model = ___\nmodel.fit(X_tr, y_tr)\nr2 = ___",
        answer="model = LinearRegression()\nmodel.fit(X_tr, y_tr)\n"
               "r2 = r2_score(y_te, model.predict(X_te))",
        check="assert r2 > 0.65, f'실제 {r2}'\nprint('통과 — R2', round(r2, 3))"),

    Task(4, "선형 회귀보다 랜덤 포레스트가 더 잘 맞히는 것을 확인한다.\n"
            "두 R² 를 `r2_lin`, `r2_rf` 에 담고 차이를 출력한다.\n"
            "> 온도와 용량의 관계가 **곡선**이라 그렇다.",
         setup=PREP + "\nfrom sklearn.linear_model import LinearRegression\n"
                      "from sklearn.ensemble import RandomForestRegressor\n"
                      "from sklearn.metrics import r2_score\n"
                      "X_tr, X_te, y_tr, y_te = split(target='방전용량')",
         answer="r2_lin = r2_score(y_te, LinearRegression().fit(X_tr, y_tr).predict(X_te))\n"
                "r2_rf = r2_score(y_te, RandomForestRegressor(n_estimators=200, random_state=42)\n"
                "                       .fit(X_tr, y_tr).predict(X_te))\n"
                "print(round(r2_lin, 3), round(r2_rf, 3), '차이', round(r2_rf - r2_lin, 3))",
         check="assert r2_rf > r2_lin, '포레스트가 더 높아야 한다'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "5. 종합 문제"),

    Task(5, "**놓친 불량을 줄이는** 쪽으로 판정 기준을 옮긴다.\n"
            "`predict_proba` 로 양품 확률을 얻고, 기준을 0.5 대신 **0.7** 로 올려\n"
            "불량 재현율이 오르는지 확인한다.\n"
            "> 확률이 0.7 미만이면 불량으로 본다.",
         setup=PREP + "\nfrom sklearn.ensemble import RandomForestClassifier\n"
                      "from sklearn.metrics import recall_score, precision_score\n"
                      "X_tr, X_te, y_tr, y_te = split()\n"
                      "model = RandomForestClassifier(n_estimators=200, random_state=42).fit(X_tr, y_tr)\n"
                      "proba = model.predict_proba(X_te)[:, 1]",
         answer="base = (proba >= 0.5).astype(int)\nstrict = (proba >= 0.7).astype(int)\n"
                "r0 = recall_score(y_te, base, pos_label=0)\n"
                "r1 = recall_score(y_te, strict, pos_label=0)\n"
                "p0 = precision_score(y_te, base, pos_label=0)\n"
                "p1 = precision_score(y_te, strict, pos_label=0)\n"
                "print(f'기준 0.5 — 재현율 {r0:.3f} 정밀도 {p0:.3f}')\n"
                "print(f'기준 0.7 — 재현율 {r1:.3f} 정밀도 {p1:.3f}')",
         check="assert r1 >= r0, '기준을 올리면 불량을 더 많이 잡는다'\n"
               "assert p1 <= p0, '대신 헛경보가 늘어 정밀도는 떨어진다'\nprint('통과')"),

    Task(6, "어떤 열이 없어도 되는지 본다.\n"
            "`성형압력` 을 **뺀 채로** 랜덤 포레스트를 학습해 정확도가 거의 그대로인 것을 확인한다.\n"
            "> `성형압력` 는 용량과 상관이 −0.05 였다.",
         setup=PREP + "\nfrom sklearn.ensemble import RandomForestClassifier\n"
                      "X_tr, X_te, y_tr, y_te = split()",
         answer="full = RandomForestClassifier(n_estimators=200, random_state=42)\\\n"
                "        .fit(X_tr, y_tr).score(X_te, y_te)\n"
                "less = RandomForestClassifier(n_estimators=200, random_state=42)\\\n"
                "        .fit(X_tr.drop(columns=['성형압력']), y_tr)\\\n"
                "        .score(X_te.drop(columns=['성형압력']), y_te)\n"
                "print(round(full, 3), round(less, 3), '차이', round(full - less, 3))",
         check="assert abs(full - less) < 0.03, f'press 를 빼도 크게 안 변한다: {full} vs {less}'\nprint('통과')"),
]

MODES = {
    # 1. 학습의 원리
    ("ex", 1): "together", ("ex", 2): "together",
    # 2. scikit-learn
    ("ex", 4): "together", ("ex", 5): "solo", ("ex", 6): "solo", ("task", 1): "team",
    # 3. 검증과 평가
    ("ex", 7): "together", ("ex", 8): "solo", ("ex", 9): "solo", ("task", 3): "team",
    # 4. 회귀
    ("ex", 10): "solo", ("task", 4): "team",
    # 5. 종합
    ("task", 5): "team", ("task", 6): "team",
}

SPEC = ("머신러닝", "경사 하강법 · scikit-learn · 검증과 평가 · 회귀", CELLS, MODES)
