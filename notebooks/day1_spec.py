"""Day 1 — 파이썬 문법 실습 스펙"""
from nbkit import md, code, h, lab, Ex, Task

CELLS = [
    # ══════════════════════════════════════════════════════════════════
    h(2, "1. 값과 변수"),

    lab("파이썬이 다루는 값의 종류를 확인한다. `type()` 이 자료형을 알려 준다."),
    code("""
print(22,      type(22))
print(7.25,    type(7.25))
print("Owen",  type("Owen"))
print(True,    type(True))
print([22, 38], type([22, 38]))
"""),

    lab("따옴표 안은 전부 글자다. 같은 `+` 라도 자료형에 따라 하는 일이 다르다."),
    code("""
print(1234 + 5)        # 덧셈
print("1234" + "5")    # 이어 붙이기
print("3" * 2)         # 두 번 반복
"""),

    Ex(1, "`n` 을 정수로 바꿔 `10` 을 더한 값을 `total` 에 담는다.",
       setup='n = "32"',
       blank="total = ___",
       answer="total = int(n) + 10",
       check='assert total == 42, f"기대 42, 실제 {total}"\nprint("통과")'),

    lab("나눗셈이 세 가지다. `/` 는 나누어 떨어져도 실수를 준다."),
    code("""
print(7 / 2)    # 나누기 — 항상 float
print(7 // 2)   # 몫만
print(7 % 2)    # 나머지
print(2 ** 10)  # 거듭제곱
"""),

    Ex(2, "초 단위 `sec` 를 `분`과 `초`로 나눠 담는다. 둘 다 정수여야 한다.",
       setup="sec = 197",
       blank="minutes = ___\nseconds = ___",
       answer="minutes = sec // 60\nseconds = sec % 60",
       check='assert (minutes, seconds) == (3, 17), f"기대 (3, 17), 실제 {(minutes, seconds)}"\nprint("통과")'),

    lab("문자열도 순서를 가진다. 인덱스는 0부터, 마지막은 -1이다."),
    code("""
name = "Braund, Mr. Owen"
print(name[0], name[-1])
print(name[8:11])       # 8 이상 11 미만
print(len(name))
print(name.upper())
print(name.split(", "))
"""),

    Ex(3, "`code` 에서 연도만 잘라 `year` 에 담는다. 결과는 문자열 `'2024'` 다.",
       setup='code = "PM-2024-A17"',
       blank="year = ___",
       answer="year = code[3:7]",
       check='assert year == "2024", f"기대 2024, 실제 {year}"\nprint("통과")'),

    Ex(4, "`raw` 의 양끝 공백을 없애고 모두 소문자로 바꿔 `clean` 에 담는다.",
       setup='raw = "   Female  "',
       blank="clean = ___",
       answer="clean = raw.strip().lower()",
       check='assert clean == "female", f"기대 female, 실제 {clean!r}"\nprint("통과")'),

    md("### 불변과 가변"),
    lab("`b = a` 는 복사가 아니다. 이름을 하나 더 붙일 뿐이다. 두 결과를 비교한다."),
    code("""
a = 10
b = a
b = b + 5
print("불변:", a, b)      # 값이 갈라진다

a = [1, 2]
b = a
b.append(3)
print("가변:", a, b)      # 같이 바뀐다
print("같은 객체인가:", id(a) == id(b))
"""),

    Ex(5, "`origin` 을 건드리지 않고 값을 추가한 새 리스트를 `copy_` 에 만든다.",
       setup="origin = [1, 2, 3]",
       blank="copy_ = ___\ncopy_.append(99)",
       answer="copy_ = origin.copy()\ncopy_.append(99)",
       check='assert origin == [1, 2, 3], f"원본이 바뀌었다: {origin}"\n'
             'assert copy_ == [1, 2, 3, 99], f"기대 [1,2,3,99], 실제 {copy_}"\nprint("통과")'),

    lab("`.copy()` 는 얕은 복사다. 안쪽에 또 자료 구조가 있으면 그건 공유된다."),
    code("""
import copy

rows = [{"name": "Owen", "age": 22}, {"name": "Laina", "age": 26}]

shallow = rows.copy()
shallow[0]["age"] = 99
print("얕은 복사 후 원본:", rows[0]["age"])   # 99 — 원본도 바뀐다

rows[0]["age"] = 22                            # 되돌리고
deep = copy.deepcopy(rows)
deep[0]["age"] = 99
print("깊은 복사 후 원본:", rows[0]["age"])   # 22 — 그대로
"""),

    Ex(6, "`board` 를 고쳐도 `origin` 이 안 바뀌게 `safe` 를 만든다.",
       setup="origin = [[1, 2], [3, 4]]\nimport copy",
       blank="safe = ___\nsafe[0][0] = 99",
       answer="safe = copy.deepcopy(origin)\nsafe[0][0] = 99",
       check='assert origin == [[1, 2], [3, 4]], f"원본이 바뀌었다: {origin}"\nprint("통과")'),

    Task(1, "이름과 나이를 받아 `\"Owen(22세)\"` 형태의 문자열을 돌려주는 코드를 쓴다.\n"
            "> `label` 변수에 담는다. f-string 을 쓰면 짧다.",
         setup='name = "Owen"\nage = 22',
         answer='label = f"{name}({age}세)"',
         check='assert label == "Owen(22세)", f"기대 Owen(22세), 실제 {label!r}"\nprint("통과")'),

    Task(2, "`price` 를 천 단위 쉼표가 붙은 문자열로 만든다. 결과는 `'1,234,567원'` 이다.\n"
            "> `f\"{값:,}\"` 형식을 쓰면 쉼표가 붙는다.",
         setup="price = 1234567",
         answer='text = f"{price:,}원"',
         check='assert text == "1,234,567원", f"기대 1,234,567원, 실제 {text!r}"\nprint("통과")'),

    # ══════════════════════════════════════════════════════════════════
    h(2, "2. 자료 구조"),

    lab("리스트는 순서가 있고 나중에 고칠 수 있다."),
    code("""
ages = [22, 38, 26, 35]

print(ages[0], ages[-1])
print(ages[1:3])
ages.append(54)
ages[1] = 39
ages.remove(26)
ages.sort()
print(ages, len(ages), 22 in ages)
"""),

    Ex(7, "`scores` 에서 가장 큰 값과 가장 작은 값의 차이를 `gap` 에 담는다.",
       setup="scores = [88, 95, 72, 100, 64]",
       blank="gap = ___",
       answer="gap = max(scores) - min(scores)",
       check='assert gap == 36, f"기대 36, 실제 {gap}"\nprint("통과")'),

    Ex(8, "`nums` 를 큰 값부터 정렬한 새 리스트를 `desc` 에 담는다. 원본은 그대로 둔다.",
       setup="nums = [3, 1, 4, 1, 5]",
       blank="desc = ___",
       answer="desc = sorted(nums, reverse=True)",
       check='assert desc == [5, 4, 3, 1, 1], f"기대 [5,4,3,1,1], 실제 {desc}"\n'
             'assert nums == [3, 1, 4, 1, 5], f"원본이 바뀌었다: {nums}"\nprint("통과")'),

    lab("튜플은 고쳐지지 않고, 집합은 중복이 사라진다."),
    code("""
shape = (891, 12)
print(shape[0])
try:
    shape[0] = 100
except TypeError as e:
    print("에러:", e)

ports = ["S", "C", "S", "Q", "S"]
print(set(ports), len(set(ports)))
"""),

    Ex(9, "`words` 에 서로 다른 단어가 몇 개인지 세어 `kinds` 에 담는다.",
       setup='words = ["red", "blue", "red", "green", "blue", "red"]',
       blank="kinds = ___",
       answer="kinds = len(set(words))",
       check='assert kinds == 3, f"기대 3, 실제 {kinds}"\nprint("통과")'),

    lab("딕셔너리는 순서가 아니라 이름으로 값을 꺼낸다."),
    code("""
row = {"name": "Owen", "age": 22, "fare": 7.25}

print(row["age"])
row["survived"] = 0
print(list(row.keys()))
print(row.get("cabin", "미상"))     # 없는 키는 기본값으로

for k, v in row.items():
    print(k, "→", v)
"""),

    Ex(10, "`config` 에서 은닉층 목록의 **첫 번째 값**을 `first` 에 담는다.",
        setup='config = {"lr": 0.001, "epochs": 50, "hidden": [64, 32]}',
        blank="first = ___",
        answer='first = config["hidden"][0]',
        check='assert first == 64, f"기대 64, 실제 {first}"\nprint("통과")'),

    lab("표 한 장은 딕셔너리의 리스트로 표현된다. Pandas 의 DataFrame 이 이 구조를 감싼 것이다."),
    code("""
rows = [
    {"name": "Owen",     "age": 22, "survived": 0},
    {"name": "Florence", "age": 38, "survived": 1},
    {"name": "Laina",    "age": 26, "survived": 1},
]
print(rows[1]["name"])
print(len(rows))
"""),

    Ex(11, "`rows` 에서 생존자(`survived == 1`)가 몇 명인지 세어 `alive` 에 담는다.",
        setup="""rows = [
    {"name": "Owen",     "age": 22, "survived": 0},
    {"name": "Florence", "age": 38, "survived": 1},
    {"name": "Laina",    "age": 26, "survived": 1},
]""",
        blank="alive = 0\nfor r in rows:\n    ___",
        answer="alive = 0\nfor r in rows:\n    if r['survived'] == 1:\n        alive = alive + 1",
        check='assert alive == 2, f"기대 2, 실제 {alive}"\nprint("통과")'),

    Task(3, "`rows` 에서 **이름만 모은 리스트**를 `names` 에 만든다.",
         setup="""rows = [
    {"name": "Owen",     "age": 22, "survived": 0},
    {"name": "Florence", "age": 38, "survived": 1},
    {"name": "Laina",    "age": 26, "survived": 1},
]""",
         answer='names = [r["name"] for r in rows]',
         check='assert names == ["Owen", "Florence", "Laina"], f"실제 {names}"\nprint("통과")'),

    Task(4, "`stock` 에서 **수량이 0인 품목의 이름**만 골라 `sold_out` 에 담는다.",
         setup='stock = {"연필": 12, "지우개": 0, "자": 5, "컴퍼스": 0}',
         answer='sold_out = [k for k, v in stock.items() if v == 0]',
         check='assert sold_out == ["지우개", "컴퍼스"], f"기대 [\'지우개\', \'컴퍼스\'], 실제 {sold_out}"\nprint("통과")'),

    # ══════════════════════════════════════════════════════════════════
    h(2, "3. 흐름 제어"),

    lab("비교식의 결과는 True / False 두 값뿐이다. 이것이 조건문의 입력이 된다."),
    code("""
age = 22
print(age < 18, type(age < 18))
print("Male" == "male")          # 대소문자를 구분한다
print(18 <= age < 65)            # 범위는 이어 쓴다
print(age > 20 and age < 30)
print(age < 18 or age > 60)
print(not (age < 18))
"""),

    Ex(12, "나이가 18 이상 65 미만이면 True 가 되도록 `is_adult` 를 만든다.",
        setup="age = 42",
        blank="is_adult = ___",
        answer="is_adult = 18 <= age < 65",
        check='assert is_adult is True, f"기대 True, 실제 {is_adult}"\n'
              'age = 70\nassert not (18 <= age < 65), "조건식을 다시 확인한다"\nprint("통과")'),

    lab("0, 빈 문자열, 빈 리스트는 거짓으로 취급된다."),
    code("""
for value in [0, 0.0, "", [], {}, None, 1, "a", [0]]:
    print(repr(value), "→", bool(value))
"""),

    lab("조건이 셋 이상이면 elif 로 잇는다. 위에서부터 걸리는 첫 줄만 실행된다."),
    code("""
def group_of(age):
    if age < 13:
        return "어린이"
    elif age < 20:
        return "청소년"
    elif age < 65:
        return "성인"
    return "노년"

for a in [7, 15, 42, 70]:
    print(a, group_of(a))
"""),

    Ex(13, "점수를 등급으로 바꾼다. 90 이상 A, 80 이상 B, 70 이상 C, 나머지 D.",
        setup="score = 85",
        blank="if ___:\n    grade = 'A'\nelif ___:\n    grade = 'B'\nelif ___:\n    grade = 'C'\nelse:\n    grade = 'D'",
        answer="if score >= 90:\n    grade = 'A'\nelif score >= 80:\n    grade = 'B'\nelif score >= 70:\n    grade = 'C'\nelse:\n    grade = 'D'",
        check='assert grade == "B", f"기대 B, 실제 {grade}"\nprint("통과")'),

    lab("반복문은 꺼낼 대상이 있을 때 for, 끝을 조건이 정할 때 while 이다."),
    code("""
ages = [22, 38, 26]

for a in ages:
    print("나이:", a)

for i, a in enumerate(ages, start=1):
    print(i, a)

for i in range(1, 6):
    print("*" * i)
"""),

    Ex(14, "1부터 100까지 더한 값을 `total` 에 담는다. `range` 를 쓴다.",
        setup="total = 0",
        blank="for i in ___:\n    total = total + i",
        answer="for i in range(1, 101):\n    total = total + i",
        check='assert total == 5050, f"기대 5050, 실제 {total}"\nprint("통과")'),

    Ex(15, "`temps` 에서 30 이상인 값만 골라 `hot` 에 담는다. 반복문과 조건문을 쓴다.",
        setup="temps = [28, 31, 25, 35, 30, 19]\nhot = []",
        blank="for t in temps:\n    ___",
        answer="for t in temps:\n    if t >= 30:\n        hot.append(t)",
        check='assert hot == [31, 35, 30], f"기대 [31,35,30], 실제 {hot}"\nprint("통과")'),

    lab("break 는 반복 자체를 끝내고, continue 는 이번 회차만 건너뛴다."),
    code("""
ages = [22, 38, 4, 35]

for a in ages:
    if a < 18:
        print("미성년 발견:", a)
        break
    print("확인:", a)

print("---")
for a in ages:
    if a < 18:
        continue
    print("집계:", a)
"""),

    Ex(16, "`nums` 를 앞에서부터 보다가 **처음 만나는 음수**를 `found` 에 담고 멈춘다.",
        setup="nums = [4, 7, 2, -3, 9, -8]\nfound = None",
        blank="for n in nums:\n    ___",
        answer="for n in nums:\n    if n < 0:\n        found = n\n        break",
        check='assert found == -3, f"기대 -3, 실제 {found}"\nprint("통과")'),

    md("### 컴프리헨션"),
    lab("반복문을 한 줄로 접는다. 괄호가 결과 자료형을 정한다."),
    code("""
names = ["Owen", "Florence", "Laina"]
ages  = [22, 38, 26]

print([n.upper() for n in names])                        # list
print({n: a for n, a in zip(names, ages)})               # dict
print({a // 10 * 10 for a in [22, 38, 26, 25, 31]})      # set
print(sum(a * 12 for a in ages))                         # generator
print([a for a in ages if a >= 26])                      # 조건으로 거르기
"""),

    Ex(17, "`nums` 의 각 값을 제곱한 리스트를 컴프리헨션으로 `squares` 에 담는다.",
        setup="nums = [1, 2, 3, 4, 5]",
        blank="squares = ___",
        answer="squares = [n ** 2 for n in nums]",
        check='assert squares == [1, 4, 9, 16, 25], f"기대 [1,4,9,16,25], 실제 {squares}"\nprint("통과")'),

    Ex(18, "`nums` 에서 짝수만 골라 리스트로 `evens` 에 담는다. 컴프리헨션을 쓴다.",
        setup="nums = [1, 2, 3, 4, 5, 6, 7, 8]",
        blank="evens = ___",
        answer="evens = [n for n in nums if n % 2 == 0]",
        check='assert evens == [2, 4, 6, 8], f"기대 [2,4,6,8], 실제 {evens}"\nprint("통과")'),

    Ex(19, "범주 목록을 `{'S': 0, 'C': 1, 'Q': 2}` 형태의 대응표로 만든다. 딕셔너리 컴프리헨션을 쓴다.",
        setup='ports = ["S", "C", "Q"]',
        blank="mapping = ___",
        answer="mapping = {v: i for i, v in enumerate(ports)}",
        check='assert mapping == {"S": 0, "C": 1, "Q": 2}, f"기대 {{\'S\':0,\'C\':1,\'Q\':2}}, 실제 {mapping}"\nprint("통과")'),

    Task(5, "1부터 30까지 중 **3의 배수만** 골라 `triples` 에 담는다.",
         setup="",
         answer="triples = [n for n in range(1, 31) if n % 3 == 0]",
         check='assert triples == [3,6,9,12,15,18,21,24,27,30], f"실제 {triples}"\nprint("통과")'),

    Task(6, "구구단 3단을 `\"3 x 1 = 3\"` 형태의 문자열 목록으로 만들어 `lines` 에 담는다.",
         setup="",
         answer='lines = [f"3 x {i} = {3 * i}" for i in range(1, 10)]',
         check='assert len(lines) == 9, f"9줄이어야 한다. 실제 {len(lines)}줄"\n'
               'assert lines[0] == "3 x 1 = 3", f"첫 줄 기대 \'3 x 1 = 3\', 실제 {lines[0]!r}"\n'
               'assert lines[-1] == "3 x 9 = 27", f"끝 줄 기대 \'3 x 9 = 27\', 실제 {lines[-1]!r}"\nprint("통과")'),

    Task(7, "`nums` 를 앞에서부터 더하다가 **합이 100을 넘으면 멈추고**, 그때까지의 합을 `total` 에 담는다.",
         setup="nums = [30, 25, 40, 50, 10]\ntotal = 0",
         answer="for n in nums:\n    total = total + n\n    if total > 100:\n        break",
         check='assert total == 145, f"기대 145, 실제 {total}"\nprint("통과")'),

    # ══════════════════════════════════════════════════════════════════
    h(2, "4. 함수"),

    lab("내장 함수는 가져오지 않고 바로 쓴다."),
    code("""
ages = [22, 38, 26, 35]

print(len(ages), max(ages), min(ages), sum(ages))
print(sum(ages) / len(ages))     # 평균 — 내장 함수에는 없다
print(sorted(ages, reverse=True))
"""),

    lab("def 로 만든 함수는 호출해야 실행된다. return 이 값을 돌려준다."),
    code("""
def age_group(age, adult=18):
    if age < adult:
        return "미성년"
    return "성인"

print(age_group(12))
print(age_group(12, adult=10))    # 기본값을 바꿔 부른다
"""),

    Ex(20, "섭씨를 화씨로 바꾸는 함수를 만든다. 공식은 `F = C * 9/5 + 32` 다.",
        setup="",
        blank="def to_fahrenheit(c):\n    ___",
        answer="def to_fahrenheit(c):\n    return c * 9 / 5 + 32",
        check='assert to_fahrenheit(0) == 32, f"0도 → 기대 32, 실제 {to_fahrenheit(0)}"\n'
              'assert to_fahrenheit(100) == 212, f"100도 → 기대 212, 실제 {to_fahrenheit(100)}"\nprint("통과")'),

    Ex(21, "리스트를 받아 평균을 돌려주는 함수를 만든다. 빈 리스트면 `0` 을 돌려준다.",
        setup="",
        blank="def mean(values):\n    ___",
        answer="def mean(values):\n    if not values:\n        return 0\n    return sum(values) / len(values)",
        check='assert mean([2, 4, 6]) == 4, f"기대 4, 실제 {mean([2,4,6])}"\n'
              'assert mean([]) == 0, f"빈 리스트 → 기대 0, 실제 {mean([])}"\nprint("통과")'),

    lab("print 만 하는 함수는 값을 돌려주지 않는다. 그 결과를 계산에 쓰면 None 이 흐른다."),
    code("""
def show(a):
    print("성인" if a >= 18 else "미성년")

def judge(a):
    return "성인" if a >= 18 else "미성년"

r1 = show(22)
r2 = judge(22)
print("show 의 결과:", r1)     # None
print("judge 의 결과:", r2)
"""),

    lab("함수 안에서 만든 이름은 함수가 끝나면 사라진다. 가변 인자는 밖까지 바뀐다."),
    code("""
def add_one(n):
    n = n + 1
    return n

def append_one(lst):
    lst.append(1)

x = 10
add_one(x)
print("불변 인자:", x)          # 10 — 안 바뀐다

nums = [0]
append_one(nums)
print("가변 인자:", nums)       # [0, 1] — 바뀐다
"""),

    Ex(22, "원본을 건드리지 않고 값을 추가한 **새 리스트**를 돌려주는 함수를 만든다.",
        setup="",
        blank="def added(lst, value):\n    ___",
        answer="def added(lst, value):\n    new = lst.copy()\n    new.append(value)\n    return new",
        check='base = [1, 2]\nout = added(base, 3)\n'
              'assert out == [1, 2, 3], f"기대 [1,2,3], 실제 {out}"\n'
              'assert base == [1, 2], f"원본이 바뀌었다: {base}"\nprint("통과")'),

    lab("메서드는 자료형에 속한 함수다. 점 앞의 값이 첫 인자로 들어간다."),
    code("""
ages = [22, 38]
ages.append(54)          # 사실상 list.append(ages, 54)
print(ages)

name = "owen"
print(name.upper())      # 문자열에는 append 가 없다

try:
    name.append("!")
except AttributeError as e:
    print("에러:", e)
"""),

    Task(8, "숫자 목록을 받아 **최댓값과 최솟값을 뺀 나머지의 평균**을 돌려주는 함수를 만든다.\n"
            "> 값이 두 개 이하면 `0` 을 돌려준다.",
         setup="",
         answer="def trimmed_mean(values):\n"
                "    if len(values) <= 2:\n        return 0\n"
                "    rest = sorted(values)[1:-1]\n"
                "    return sum(rest) / len(rest)",
         check='assert trimmed_mean([1, 5, 6, 7, 100]) == 6, f"실제 {trimmed_mean([1,5,6,7,100])}"\n'
               'assert trimmed_mean([3, 9]) == 0, "값이 둘이면 0 이어야 한다"\nprint("통과")'),

    Task(9, "문자열을 받아 **거꾸로 읽어도 같은지** 판정하는 함수를 만든다.\n"
            "> 공백과 대소문자는 무시한다. `\"Never odd or even\"` 은 True 다.",
         setup="",
         answer='def is_palindrome(text):\n'
                '    s = text.replace(" ", "").lower()\n'
                '    return s == s[::-1]',
         check='assert is_palindrome("Never odd or even") is True, "True 여야 한다"\n'
               'assert is_palindrome("hello") is False, "False 여야 한다"\nprint("통과")'),

    # ══════════════════════════════════════════════════════════════════
    h(2, "5. 종합 문제"),
    md("앞의 내용을 섞어서 푼다. 막히면 위 실습 셀로 돌아가 확인한다."),

    Ex(23, "승객 목록에서 **여성 생존율**을 구해 `rate` 에 담는다. 소수 그대로 둔다.",
        setup="""passengers = [
    {"name": "Owen",     "sex": "male",   "survived": 0},
    {"name": "Florence", "sex": "female", "survived": 1},
    {"name": "Laina",    "sex": "female", "survived": 1},
    {"name": "William",  "sex": "male",   "survived": 0},
    {"name": "Lily",     "sex": "female", "survived": 0},
]""",
        blank="females = ___\nrate = ___",
        answer='females = [p for p in passengers if p["sex"] == "female"]\n'
               'rate = sum(p["survived"] for p in females) / len(females)',
        check='assert abs(rate - 2/3) < 1e-9, f"기대 0.666…, 실제 {rate}"\nprint("통과")'),

    Ex(24, "나이 목록에서 결측(`None`)을 뺀 나머지의 평균을 `avg` 에 담는다.",
        setup="raw_ages = [22, None, 38, 26, None, 35]",
        blank="valid = ___\navg = ___",
        answer="valid = [a for a in raw_ages if a is not None]\navg = sum(valid) / len(valid)",
        check='assert avg == 30.25, f"기대 30.25, 실제 {avg}"\nprint("통과")'),

    Ex(25, "단어 목록에서 **각 단어가 몇 번 나왔는지** 세어 딕셔너리 `counts` 를 만든다.",
        setup='words = ["red", "blue", "red", "green", "blue", "red"]\ncounts = {}',
        blank="for w in words:\n    ___",
        answer="for w in words:\n    counts[w] = counts.get(w, 0) + 1",
        check='assert counts == {"red": 3, "blue": 2, "green": 1}, f"기대 {{\'red\':3,\'blue\':2,\'green\':1}}, 실제 {counts}"\nprint("통과")'),

    Ex(26, "점수 목록을 받아 `{\"A\": n, \"B\": n, ...}` 형태로 등급 분포를 돌려주는 함수를 만든다.\n"
           "> 90↑ A · 80↑ B · 70↑ C · 나머지 D. 한 명도 없는 등급은 키에 넣지 않는다.",
        setup="",
        blank="def grade_counts(scores):\n    ___",
        answer="def grade_counts(scores):\n"
               "    result = {}\n"
               "    for s in scores:\n"
               "        if s >= 90:\n            g = 'A'\n"
               "        elif s >= 80:\n            g = 'B'\n"
               "        elif s >= 70:\n            g = 'C'\n"
               "        else:\n            g = 'D'\n"
               "        result[g] = result.get(g, 0) + 1\n"
               "    return result",
        check='out = grade_counts([95, 82, 71, 64, 88, 91])\n'
              'assert out == {"A": 2, "B": 2, "C": 1, "D": 1}, f"실제 {out}"\n'
              'assert grade_counts([]) == {}, "빈 목록은 빈 딕셔너리여야 한다"\nprint("통과")'),

    Task(10, "승객 목록을 받아 **성별 생존율 딕셔너리**를 돌려주는 함수를 만든다.\n"
             "> 결과는 `{\"male\": 0.0, \"female\": 0.666…}` 형태다.",
         setup="""passengers = [
    {"name": "Owen",     "sex": "male",   "survived": 0},
    {"name": "Florence", "sex": "female", "survived": 1},
    {"name": "Laina",    "sex": "female", "survived": 1},
    {"name": "William",  "sex": "male",   "survived": 0},
    {"name": "Lily",     "sex": "female", "survived": 0},
]""",
         answer='def survival_by_sex(rows):\n'
                '    result = {}\n'
                '    for sex in set(r["sex"] for r in rows):\n'
                '        group = [r for r in rows if r["sex"] == sex]\n'
                '        result[sex] = sum(r["survived"] for r in group) / len(group)\n'
                '    return result',
         check='out = survival_by_sex(passengers)\n'
               'assert set(out.keys()) == {"male", "female"}, f"키가 다르다: {out.keys()}"\n'
               'assert out["male"] == 0.0, f"male 기대 0.0, 실제 {out[\'male\']}"\n'
               'assert abs(out["female"] - 2/3) < 1e-9, f"female 기대 0.666…, 실제 {out[\'female\']}"\nprint("통과")'),

    Task(11, "나이 목록을 받아 **연령대별 인원수**를 돌려주는 함수를 만든다.\n"
             "> `[22, 38, 26, 35, 41]` → `{20: 2, 30: 2, 40: 1}`. 결측(`None`)은 건너뛴다.",
         setup="",
         answer="def by_decade(ages):\n"
                "    result = {}\n"
                "    for a in ages:\n"
                "        if a is None:\n            continue\n"
                "        d = a // 10 * 10\n"
                "        result[d] = result.get(d, 0) + 1\n"
                "    return result",
         check='assert by_decade([22, 38, 26, 35, 41]) == {20: 2, 30: 2, 40: 1}, f"실제 {by_decade([22,38,26,35,41])}"\n'
               'assert by_decade([22, None, 25]) == {20: 3} or by_decade([22, None, 25]) == {20: 2}, "결측을 건너뛰어야 한다"\n'
               'assert by_decade([22, None, 25]) == {20: 2}, f"결측 제외 후 기대 {{20: 2}}, 실제 {by_decade([22, None, 25])}"\nprint("통과")'),

    md("""
---

수고했다. 여기까지 통과했으면 남은 사흘의 코드를 따라 읽을 준비가 된 것이다.
"""),
]

# 문제별 진행 방식 — 섹션 첫 문제는 수업 중에 같이, 종합·어려운 것은 조별
MODES = {
    # 1. 값과 변수
    ("ex", 1): "together",   ("ex", 5): "together",
    ("task", 1): "solo",     ("task", 2): "team",
    # 2. 자료 구조
    ("ex", 7): "together",   ("ex", 10): "together",
    ("task", 3): "solo",     ("task", 4): "team",
    # 3. 흐름 제어
    ("ex", 12): "together",  ("ex", 14): "together",  ("ex", 17): "together",
    ("task", 5): "solo",     ("task", 6): "team",     ("task", 7): "team",
    # 4. 함수
    ("ex", 20): "together",
    ("task", 8): "team",     ("task", 9): "team",
    # 5. 종합 — 전부 조별
    ("ex", 23): "team",  ("ex", 24): "team",  ("ex", 25): "team",  ("ex", 26): "team",
    ("task", 10): "team",    ("task", 11): "team",
}

SPEC = ("파이썬 문법", "값과 변수 · 자료 구조 · 흐름 제어 · 함수", CELLS, MODES)
