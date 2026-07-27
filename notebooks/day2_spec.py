"""Day 2 — 데이터 다루기 실습 스펙 (NumPy · Pandas · 전처리 · 시각화)"""
from nbkit import md, code, h, lab, Ex, Task

URL = "https://tunalee.github.io/posco/data/batch_quality.csv"
MASTER = "https://tunalee.github.io/posco/data/line_master.csv"

# 문제 셀마다 데이터를 다시 읽어 앞 문제의 결과에 기대지 않게 한다.
LOAD = (
    "import pandas as pd\n"
    f"df = pd.read_csv('{URL}', thousands=',', na_values=['N/A', '-'])\n"
    "df['line'] = df['line'].str.strip().str.upper()"
)

CELLS = [
    # ══════════════════════════════════════════════════════════════════
    h(2, "0. NumPy"),

    lab("배열은 원소마다 연산이 걸린다. 리스트와 가장 크게 다른 점이다."),
    code("""
import numpy as np

a = [1, 2, 3]
b = np.array([1, 2, 3])

print(a * 2)      # 리스트 — 이어 붙는다
print(b * 2)      # 배열 — 원소마다 곱해진다
print(b + 1)
"""),

    Ex(1, "`temps` 를 배열로 만들고 전부 화씨로 바꿔 `f` 에 담는다. 화씨 = 섭씨 × 9/5 + 32.",
       setup="import numpy as np\ntemps = [898, 835, 829]",
       blank="c = np.array(temps)\nf = ___",
       answer="c = np.array(temps)\nf = c * 9 / 5 + 32",
       check="assert list(f.round(1)) == [1648.4, 1535.0, 1524.2], f'실제 {list(f.round(1))}'\nprint('통과')"),

    lab("`shape` 는 각 축의 길이를 튜플로 알려 준다. `reshape` 로 모양을 바꾼다."),
    code("""
import numpy as np

X = np.arange(12)
print(X.shape)

X = X.reshape(3, 4)
print(X.shape)
print(X)

print(X.reshape(-1, 2).shape)   # -1 은 알아서 계산
"""),

    Ex(2, "`X` 를 6행짜리로 바꿔 `Y` 에 담는다. 열 수는 `-1` 로 맡긴다.",
       setup="import numpy as np\nX = np.arange(24)",
       blank="Y = ___",
       answer="Y = X.reshape(6, -1)",
       check="assert Y.shape == (6, 4), f'기대 (6, 4), 실제 {Y.shape}'\nprint('통과')"),

    lab("대괄호에 숫자를 넣으면 위치, 불리언 배열을 넣으면 조건이다."),
    code("""
import numpy as np

X = np.arange(12).reshape(3, 4)
print(X[0, 2])      # 한 값
print(X[1])         # 행 하나
print(X[:, 0])      # 열 하나
print(X[0:2, 1:3])  # 사각형 구간

a = np.array([898, 835, 760, 860])
print(a >= 800)
print(a[a >= 800])
"""),

    Ex(3, "`a` 에서 800 미만인 값만 골라 `low` 에 담는다. 반복문을 쓰지 않는다.",
       setup="import numpy as np\na = np.array([898, 835, 760, 860, 781])",
       blank="low = ___",
       answer="low = a[a < 800]",
       check="assert list(low) == [760, 781], f'실제 {list(low)}'\nprint('통과')"),

    Ex(4, "`a` 에서 800 이상인 값들의 **평균**을 `avg` 에 담는다.",
       setup="import numpy as np\na = np.array([898, 835, 760, 860, 781])",
       blank="avg = ___",
       answer="avg = a[a >= 800].mean()",
       check="assert abs(avg - 864.3333333333334) < 1e-9, f'실제 {avg}'\nprint('통과')"),

    lab("모양이 다른 배열끼리도 규칙이 맞으면 계산된다. 브로드캐스팅이라 한다."),
    code("""
import numpy as np

X = np.arange(6).reshape(2, 3)
print(X + 10)              # 스칼라가 모든 원소로 퍼진다
print(X + np.array([1, 2, 3]))   # 행마다 같은 벡터를 더한다

W = np.array([[1], [2], [3]])
print(X @ W)               # 행렬 곱 — (2,3) @ (3,1) = (2,1)
"""),

    Task(1, "`X` 의 **각 열을 평균 0으로** 맞춘 배열을 `Z` 에 담는다.\n"
            "> 열별 평균은 `X.mean(axis=0)` 이다. 브로드캐스팅으로 한 줄에 끝난다.",
         setup="import numpy as np\nX = np.array([[1., 2., 3.], [5., 6., 7.]])",
         answer="Z = X - X.mean(axis=0)",
         check="assert np.allclose(Z.mean(axis=0), [0, 0, 0]), f'열 평균이 0이 아니다: {Z.mean(axis=0)}'\n"
               "assert Z.shape == X.shape\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "1. Pandas — 읽고 확인하기"),

    lab("CSV 를 읽어 표로 만든다. 인터넷 주소도 경로처럼 넣는다."),
    code(f"""
import pandas as pd

url = '{URL}'
raw = pd.read_csv(url)

print(raw.shape)
raw.head(3)
"""),

    lab("읽자마자 타입을 본다. 숫자여야 할 열이 object 면 손봐야 한다."),
    code("""
raw.info()
"""),

    lab("쉼표와 결측 표기를 알려 주고 다시 읽으면 타입이 잡힌다."),
    code(f"""
df = pd.read_csv('{URL}',
                 thousands=',',            # '1,024' → 1024
                 na_values=['N/A', '-'])   # 결측 표기

print(df.dtypes)
print(df.isna().sum())
"""),

    Ex(5, "`df` 에서 **행 수**를 `n_rows`, **열 수**를 `n_cols` 에 담는다.",
       setup=LOAD,
       blank="n_rows = ___\nn_cols = ___",
       answer="n_rows = df.shape[0]\nn_cols = df.shape[1]",
       check="assert (n_rows, n_cols) == (1412, 11), f'실제 {(n_rows, n_cols)}'\nprint('통과')"),

    Ex(6, "결측이 하나라도 있는 열의 **이름 목록**을 `missing_cols` 에 담는다.",
       setup=LOAD,
       blank="missing_cols = ___",
       answer="missing_cols = list(df.columns[df.isna().sum() > 0])",
       check="assert sorted(missing_cols) == ['moisture', 'particle_size'], f'실제 {missing_cols}'\nprint('통과')"),

    lab("범주형 열은 value_counts 로 먼저 본다. 표기 흔들림이 여기서 드러난다."),
    code(f"""
raw = pd.read_csv('{URL}')
print(raw['line'].value_counts().head(8))
print('종류 수:', raw['line'].nunique())

cleaned = raw['line'].str.strip().str.upper()
print('정리 후 종류 수:', cleaned.nunique())
"""),

    Ex(7, "`raw['line']` 의 공백과 대소문자를 정리해 `n_kind` 에 **종류 수**를 담는다.",
       setup=f"import pandas as pd\nraw = pd.read_csv('{URL}')",
       blank="n_kind = ___",
       answer="n_kind = raw['line'].str.strip().str.upper().nunique()",
       check="assert n_kind == 6, f'기대 6, 실제 {n_kind}'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "2. Pandas — 고르고 계산하기"),

    lab("대괄호 하나는 Series, 둘은 DataFrame 이다. 조건식을 넣으면 행이 걸러진다."),
    code(f"""
{LOAD}

print(type(df['calc_temp']))
print(type(df[['calc_temp']]))

print(df[df['capacity'] < 168].shape)
print(df[(df['capacity'] < 168) & (df['line'] == 'A')].shape)
"""),

    Ex(8, "불량(`passed == 0`)인 행만 골라 `bad` 에 담는다.",
       setup=LOAD,
       blank="bad = ___",
       answer="bad = df[df['passed'] == 0]",
       check="assert len(bad) == 265, f'기대 265, 실제 {len(bad)}'\nprint('통과')"),

    Ex(9, "`calc_temp` 가 900 이상이면서 양품인 배치 수를 `n` 에 담는다.",
       setup=LOAD,
       blank="n = ___",
       answer="n = len(df[(df['calc_temp'] >= 900) & (df['passed'] == 1)])",
       check="assert n == 65, f'기대 65, 실제 {n}'\nprint('통과')"),

    lab("`loc` 는 이름으로, `iloc` 는 번호로 고른다. 슬라이스의 끝 처리가 다르다."),
    code(f"""
{LOAD}

print(df.loc[0, 'calc_temp'])
print(df.loc[0:2, ['line', 'calc_temp']])   # 끝 포함
print(df.iloc[0:2, 1:4])                    # 끝 제외
"""),

    Ex(10, "`loc` 로 불량 배치의 `capacity` 만 뽑아 평균을 `avg` 에 담는다.",
       setup=LOAD,
       blank="avg = ___",
       answer="avg = df.loc[df['passed'] == 0, 'capacity'].mean()",
       check="assert abs(avg - 164.5) < 1.0, f'실제 {avg}'\nprint('통과')"),

    lab("열 전체에 한 번에 연산이 걸린다. 반복문이 필요 없다."),
    code(f"""
{LOAD}

df['temp_gap'] = (df['calc_temp'] - 890).abs()
df['is_low'] = df['capacity'] < 168

print(df[['calc_temp', 'temp_gap', 'capacity', 'is_low']].head(3))
"""),

    Ex(11, "`impurity` 를 퍼센트로 바꾼 열 `impurity_pct` 를 만든다. ppm ÷ 10000 이다.",
       setup=LOAD,
       blank="df['impurity_pct'] = ___",
       answer="df['impurity_pct'] = df['impurity'] / 10000",
       check="assert abs(df['impurity_pct'].mean() - 0.0829) < 0.001, f\"실제 {df['impurity_pct'].mean()}\"\nprint('통과')"),

    Task(2, "온도가 최적점(890 °C)에서 얼마나 벗어났는지를 `temp_gap` 열에 만들고,\n"
            "**벗어남이 가장 큰 배치 3건**의 `batch_id` 를 `worst` 에 담는다.\n"
            "> `sort_values` 와 `head(3)` 를 쓴다.",
         setup=LOAD,
         answer="df['temp_gap'] = (df['calc_temp'] - 890).abs()\n"
                "worst = list(df.sort_values('temp_gap', ascending=False).head(3)['batch_id'])",
         check="assert len(worst) == 3, f'3건이어야 한다: {worst}'\n"
               "assert df.set_index('batch_id').loc[worst[0], 'calc_temp'] < 800\nprint('통과')"),

    lab("map 은 대응표로 갈아 끼우고, apply 는 만든 함수를 태운다."),
    code(f"""
{LOAD}

df['shift_code'] = df['shift'].map({{'day': 0, 'night': 1}})

def grade(c):
    if c < 168:  return 'low'
    if c < 178:  return 'mid'
    return 'high'

df['grade'] = df['capacity'].apply(grade)
print(df['grade'].value_counts())
"""),

    Ex(12, "`line` 을 설치 연도로 바꾼 열 `year` 를 만든다.\n"
           "A·B는 2015, C·D는 2018, E·F는 2021 이다.",
        setup=LOAD,
        blank="year_map = ___\ndf['year'] = ___",
        answer="year_map = {'A': 2015, 'B': 2015, 'C': 2018, 'D': 2018, 'E': 2021, 'F': 2021}\n"
               "df['year'] = df['line'].map(year_map)",
        check="assert df['year'].isna().sum() == 0, '못 바꾼 값이 있다'\n"
              "assert sorted(df['year'].unique()) == [2015, 2018, 2021]\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "3. Pandas — 묶고 합치기"),

    lab("groupby 는 나누고 계산하고 합친다. 세 단계가 한 줄에 들어 있다."),
    code(f"""
{LOAD}

print(df.groupby('line')['passed'].mean().round(3))
print(df.groupby('shift')['calc_temp'].std().round(1))
print(df.groupby(['line', 'shift'])['capacity'].mean().round(1).head(4))
"""),

    Ex(13, "설비별 **불량률**을 구해 `bad_rate` 에 담는다. 불량률 = 1 − 양품률.",
        setup=LOAD,
        blank="bad_rate = ___",
        answer="bad_rate = 1 - df.groupby('line')['passed'].mean()",
        check="assert abs(bad_rate['A'] - 0.221) < 0.002, f\"A 실제 {bad_rate['A']}\"\n"
              "assert bad_rate.idxmax() == 'A', f'가장 나쁜 설비는 A 여야 한다: {bad_rate.idxmax()}'\nprint('통과')"),

    Ex(14, "`agg` 로 설비별 **양품률·건수·용량 중앙값**을 한 번에 낸 표를 `summary` 에 담는다.",
        setup=LOAD,
        blank="summary = df.groupby('line').agg(___)",
        answer="summary = df.groupby('line').agg({'passed': ['mean', 'count'], 'capacity': 'median'})",
        check="assert summary.shape[0] == 6, f'설비 6개여야 한다: {summary.shape}'\n"
              "assert summary.shape[1] == 3, f'열 3개여야 한다: {summary.shape}'\nprint('통과')"),

    lab("설비 마스터를 붙이면 연식이 드러난다. merge 는 키를 기준으로 옆에 잇는다."),
    code(f"""
{LOAD}
master = pd.read_csv('{MASTER}')
print(master)

merged = pd.merge(df, master, on='line', how='left')
print((1 - merged.groupby('installed_year')['passed'].mean()).round(3))
"""),

    Task(3, "설비 마스터를 붙여 **팀별 평균 용량**을 `by_team` 에 담는다.\n"
            "> `merge` 후 `groupby('team')` 이다.",
         setup=LOAD + f"\nmaster = pd.read_csv('{MASTER}')",
         answer="merged = pd.merge(df, master, on='line', how='left')\n"
                "by_team = merged.groupby('team')['capacity'].mean()",
         check="assert len(by_team) == 3, f'팀 3개여야 한다: {by_team}'\n"
               "assert by_team.idxmax() == '3팀', f'가장 높은 팀은 3팀: {by_team.idxmax()}'\nprint('통과')"),

    Task(4, "같은 배치가 두 번 기록된 행이 있다. **몇 건인지** 세어 `n_dup` 에 담고,\n"
            "지운 뒤 남는 행 수를 `n_left` 에 담는다.",
         setup=LOAD,
         answer="n_dup = df.duplicated().sum()\nn_left = len(df.drop_duplicates())",
         check="assert n_dup == 12, f'기대 12, 실제 {n_dup}'\n"
               "assert n_left == 1400, f'기대 1400, 실제 {n_left}'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "4. 전처리"),

    lab("결측은 세고, 왜 비었는지 보고, 그다음에 메운다."),
    code(f"""
{LOAD}

print(df.isna().sum())
print(df.groupby(df['particle_size'].isna())['passed'].mean().round(3))

df['particle_size'] = df['particle_size'].fillna(df['particle_size'].median())
print('메운 뒤:', df['particle_size'].isna().sum())
"""),

    Ex(15, "`moisture` 결측을 **설비별 중앙값**으로 채운다.",
        setup=LOAD,
        blank="df['moisture'] = df.groupby('line')['moisture'].transform(___)",
        answer="df['moisture'] = df.groupby('line')['moisture'].transform(lambda s: s.fillna(s.median()))",
        check="assert df['moisture'].isna().sum() == 0, '아직 결측이 남았다'\nprint('통과')"),

    lab("글자는 모델에 들어가지 않는다. 원-핫으로 열을 늘린다."),
    code(f"""
{LOAD}

d = pd.get_dummies(df, columns=['line', 'shift'], drop_first=True)
print([c for c in d.columns if c.startswith(('line_', 'shift_'))])
print(d.shape)
"""),

    Ex(16, "`line` 과 `shift` 를 원-핫으로 바꾼 표를 `d` 에 담는다. 첫 범주는 뺀다.",
        setup=LOAD,
        blank="d = ___",
        answer="d = pd.get_dummies(df, columns=['line', 'shift'], drop_first=True)",
        check="cols = [c for c in d.columns if c.startswith(('line_', 'shift_'))]\n"
              "assert len(cols) == 6, f'기대 6개, 실제 {len(cols)}: {cols}'\n"
              "assert 'line_A' not in cols, 'drop_first=True 면 line_A 는 빠진다'\nprint('통과')"),

    lab("분할이 스케일링보다 먼저다. 순서를 바꾸면 테스트셋 정보가 새어 들어간다."),
    code(f"""
{LOAD}
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

df['particle_size'] = df['particle_size'].fillna(df['particle_size'].median())
df = df.dropna(subset=['moisture'])
d = pd.get_dummies(df, columns=['line', 'shift'], drop_first=True)

X = d.drop(columns=['passed', 'capacity', 'batch_id'])
y = d['passed']

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_tr = scaler.fit_transform(X_tr)   # 훈련셋에만 fit
X_te = scaler.transform(X_te)       # 테스트셋은 transform 만

print(X_tr.shape, X_te.shape)
print('훈련셋 불량 비율:', round(1 - y_tr.mean(), 3))
print('테스트셋 불량 비율:', round(1 - y_te.mean(), 3))
"""),

    Task(5, "위 전처리를 **함수 하나로** 묶는다. `prep(url)` 이 `X_tr, X_te, y_tr, y_te` 를 돌려준다.\n"
            "> 결측 채우기 → 원-핫 → 분할 → 스케일링 순서를 지킨다.",
         setup=f"import pandas as pd\nfrom sklearn.model_selection import train_test_split\n"
               f"from sklearn.preprocessing import StandardScaler\nURL = '{URL}'",
         answer="def prep(url):\n"
                "    df = pd.read_csv(url, thousands=',', na_values=['N/A', '-'])\n"
                "    df['line'] = df['line'].str.strip().str.upper()\n"
                "    df['particle_size'] = df['particle_size'].fillna(df['particle_size'].median())\n"
                "    df = df.dropna(subset=['moisture'])\n"
                "    d = pd.get_dummies(df, columns=['line', 'shift'], drop_first=True)\n"
                "    X = d.drop(columns=['passed', 'capacity', 'batch_id'])\n"
                "    y = d['passed']\n"
                "    X_tr, X_te, y_tr, y_te = train_test_split(\n"
                "        X, y, test_size=0.2, random_state=42, stratify=y)\n"
                "    sc = StandardScaler()\n"
                "    return sc.fit_transform(X_tr), sc.transform(X_te), y_tr, y_te",
         check="a, b, c, d_ = prep(URL)\n"
               "assert a.shape[1] == b.shape[1], '훈련셋과 테스트셋의 열 수가 달라졌다'\n"
               "assert len(a) > len(b), '훈련셋이 더 커야 한다'\n"
               "assert abs((1 - c.mean()) - (1 - d_.mean())) < 0.02, 'stratify 로 비율을 맞춘다'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "5. 시각화"),

    lab("한 열의 분포는 히스토그램이다. Colab 에서 한글을 쓰려면 폰트를 깐다."),
    code(f"""
{LOAD}
import matplotlib.pyplot as plt

plt.hist(df['capacity'], bins=30)
plt.xlabel('capacity (mAh/g)')
plt.ylabel('batches')
plt.title('Discharge capacity')
plt.show()
"""),

    lab("두 열의 관계는 산점도다. 점이 겹치면 alpha 를 낮춘다."),
    code(f"""
{LOAD}
import matplotlib.pyplot as plt

plt.scatter(df['calc_temp'], df['capacity'], alpha=0.25, s=12)
plt.xlabel('calc_temp')
plt.ylabel('capacity')
plt.show()
"""),

    Ex(17, "설비별 **평균 용량**을 막대 그래프로 그린다.",
        setup=LOAD + "\nimport matplotlib.pyplot as plt",
        blank="ax = ___\nplt.show()",
        answer="ax = df.groupby('line')['capacity'].mean().plot.bar()\nplt.show()",
        check="assert ax is not None, '그래프 객체가 없다'\nprint('통과')"),

    lab("상관 히트맵으로 답과 붙어 있는 열을 찾는다."),
    code(f"""
{LOAD}
import seaborn as sns
import matplotlib.pyplot as plt

cols = ['calc_temp', 'calc_time', 'particle_size', 'moisture', 'impurity', 'press', 'capacity']
sns.heatmap(df[cols].corr(numeric_only=True), annot=True, fmt='.2f', cmap='coolwarm')
plt.show()
"""),

    Ex(18, "`capacity` 와 상관이 **가장 강한 열**의 이름을 `best` 에 담는다.\n"
           "자기 자신은 뺀다. 부호는 무시하고 절댓값으로 본다.",
        setup=LOAD,
        blank="c = df.corr(numeric_only=True)['capacity'].drop('capacity')\nbest = ___",
        answer="c = df.corr(numeric_only=True)['capacity'].drop('capacity')\nbest = c.abs().idxmax()",
        check="assert best == 'calc_temp', f'기대 calc_temp, 실제 {best}'\nprint('통과')"),

    Task(6, "설비별 `capacity` 분포를 **박스플롯**으로 그리고,\n"
            "이상치가 가장 많이 튀어나온 열이 무엇인지 눈으로 확인한다.\n"
            "> `sns.boxplot(data=df, x='line', y='capacity')`",
         setup=LOAD + "\nimport seaborn as sns\nimport matplotlib.pyplot as plt",
         answer="sns.boxplot(data=df, x='line', y='capacity')\nplt.show()",
         check="print('통과 — 그림이 그려졌으면 된다')"),

    Task(7, "`press` 에는 센서 오류값 999 가 섞여 있다.\n"
            "**999 를 결측으로 바꾼 뒤** 중앙값으로 채우고, 바꾸기 전후의 평균을 둘 다 출력한다.",
         setup=LOAD,
         answer="before = df['press'].mean()\n"
                "df.loc[df['press'] == 999, 'press'] = None\n"
                "df['press'] = df['press'].fillna(df['press'].median())\n"
                "after = df['press'].mean()\n"
                "print(round(before, 2), round(after, 2))",
         check="assert before > 30, f'바꾸기 전 평균은 999 탓에 커야 한다: {before}'\n"
               "assert 23 < after < 25, f'바꾼 뒤 평균은 24 근처: {after}'\nprint('통과')"),

    # ══════════════════════════════════════════════════════════════════
    h(2, "6. 종합 문제"),

    Ex(19, "**야간조의 불량률**과 **주간조의 불량률** 차이를 `gap` 에 담는다.\n"
           "야간 − 주간 순서로 뺀다.",
        setup=LOAD,
        blank="rate = ___\ngap = ___",
        answer="rate = 1 - df.groupby('shift')['passed'].mean()\ngap = rate['night'] - rate['day']",
        check="assert gap > 0, '야간조 불량률이 더 높다'\n"
              "assert abs(gap - 0.035) < 0.01, f'실제 {gap}'\nprint('통과')"),

    Ex(20, "온도를 10도 구간으로 묶어 구간별 **평균 용량**을 `band_avg` 에 담는다.\n"
           "> `(df['calc_temp'] // 10 * 10)` 으로 구간 열을 만든다.",
        setup=LOAD,
        blank="df['band'] = ___\nband_avg = ___",
        answer="df['band'] = df['calc_temp'] // 10 * 10\n"
               "band_avg = df.groupby('band')['capacity'].mean()",
        check="assert band_avg.idxmax() >= 880, f'용량이 가장 높은 구간은 880 이상: {band_avg.idxmax()}'\nprint('통과')"),

    Task(8, "**불량이 가장 많이 나온 조건 조합**을 찾는다.\n"
            "설비와 교대조로 묶어 불량 건수를 세고, 가장 많은 조합을 `worst` 에 담는다.\n"
            "> 결과는 `('A', 'night')` 같은 튜플이다.",
         setup=LOAD,
         answer="cnt = df[df['passed'] == 0].groupby(['line', 'shift']).size()\nworst = cnt.idxmax()",
         check="assert isinstance(worst, tuple) and len(worst) == 2, f'튜플이어야 한다: {worst}'\n"
               "assert worst[0] in list('ABCDEF') and worst[1] in ('day', 'night')\nprint('통과')"),

    Task(9, "설비 마스터를 붙여 **연식별 평균 용량과 불량률**을 한 표로 만든다.\n"
            "> `installed_year` 로 묶어 `capacity` 평균과 `passed` 평균을 같이 낸다.",
         setup=LOAD + f"\nmaster = pd.read_csv('{MASTER}')",
         answer="merged = pd.merge(df, master, on='line', how='left')\n"
                "table = merged.groupby('installed_year').agg(\n"
                "    avg_capacity=('capacity', 'mean'),\n"
                "    bad_rate=('passed', lambda s: 1 - s.mean()))\n"
                "print(table.round(3))",
         check="assert len(table) == 3, f'연식 3종: {len(table)}'\n"
               "assert table['bad_rate'].iloc[0] > table['bad_rate'].iloc[-1], '오래된 설비의 불량률이 더 높다'\n"
               "assert table['avg_capacity'].iloc[0] < table['avg_capacity'].iloc[-1]\nprint('통과')"),
]

MODES = {
    # 0. NumPy
    ("ex", 1): "together",  ("ex", 2): "together",
    ("ex", 3): "solo",      ("ex", 4): "solo",       ("task", 1): "team",
    # 1. 읽고 확인하기
    ("ex", 5): "together",  ("ex", 6): "solo",       ("ex", 7): "solo",
    # 2. 고르고 계산하기
    ("ex", 8): "together",  ("ex", 9): "solo",       ("ex", 10): "solo",
    ("ex", 11): "solo",     ("ex", 12): "solo",      ("task", 2): "team",
    # 3. 묶고 합치기
    ("ex", 13): "together", ("ex", 14): "solo",
    ("task", 3): "team",    ("task", 4): "team",
    # 4. 전처리
    ("ex", 15): "together", ("ex", 16): "solo",      ("task", 5): "team",
    # 5. 시각화
    ("ex", 17): "together", ("ex", 18): "solo",
    ("task", 6): "team",    ("task", 7): "team",
    # 6. 종합 — 전부 조별
    ("ex", 19): "team",     ("ex", 20): "team",
    ("task", 8): "team",    ("task", 9): "team",
}

SPEC = ("데이터 다루기", "NumPy · Pandas · 전처리 · 시각화", CELLS, MODES)
