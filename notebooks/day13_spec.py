"""4주차 D1 — Docker 다루기"""
from nbkit import md, code, h, lab, prep, Ex, Task

CELLS = [
    md("## 1. 이 노트북이 하는 일"),
    md("Docker 는 **Colab 에서 안 돌아간다.** 실제 명령은 **터미널에서** 친다.\n\n"
       "이 노트북은 그 앞뒤를 맡는다 &mdash;\n"
       "**무엇을 시킬지 정하고**, Codex 가 내놓은 파일을 **읽고 고치는** 연습이다.\n\n"
       "> 코드를 쓰는 문제는 없다. 고를 것을 고르고 틀린 데를 짚는 문제다."),

    prep("""# 검사에 쓸 도구만 준비한다. 설치할 것이 없다.
import re, textwrap

def 줄번호(글, 찾을것):
    for i, line in enumerate(글.strip().split('\\n'), 1):
        if 찾을것 in line:
            return i
    return None

print('준비됐다')"""),

    md("## 2. 여섯 가지 적기"),
    md("Codex 에게 시키기 전에 **여섯 가지**를 정해야 한다. 이걸 안 주면 지어낸다."),

    Task(1, "담을 앱을 하나 골라 **여섯 가지**을 채운다.\n"
            "> 2~3명이 한 조로 상의한다. 앞 회차에서 만든 것 중에 고른다.\n"
            "> 모르는 것은 비워 두지 말고 「확인 필요」라고 적는다.",
         blank="""알려줄것 = {
    '언어와 버전':  '___',
    '라이브러리':   '___',
    '시작 명령':    '___',
    '여는 포트':    '___',
    '데이터':      '___',
    '키':         '___',
}
for k, v in 알려줄것.items():
    print('%-10s %s' % (k, v))""",
         answer="""알려줄것 = {
    '언어와 버전':  '파이썬 3.12',
    '라이브러리':   'requirements.txt 에 있는 것 그대로',
    '시작 명령':    'python app.py',
    '여는 포트':    '8000',
    '데이터':      'cell_process.csv — 이미지에 넣지 않고 밖에서 물린다',
    '키':         'NVIDIA_API_KEY — 값은 주지 않는다',
}
for k, v in 알려줄것.items():
    print('%-10s %s' % (k, v))""",
         check="""assert '___' not in str(알려줄것), '여섯 가지을 다 채운다'
print()
print('빠진 것 없음. 다음 문제에서 이것을 프롬프트로 옮긴다.')"""),

    md("## 3. 프롬프트로 옮기기"),
    md("여섯 가지을 **문장으로** 바꾼다. 아래 뼈대에 값만 끼워 넣으면 된다."),

    Ex(1, "여섯 가지을 프롬프트로 만든다. **빠뜨리면 안 되는 두 줄**이 뒤에 있다.\n"
          "> 그 두 줄이 없으면 Codex 가 늘 같은 실수를 한다.",
       setup="# 알려줄것 을 그대로 쓴다",
       blank="""프롬프트 = f'''Dockerfile 을 만들어 줘.

{알려줄것['언어와 버전']} 을 쓴다. 바탕 이미지는 slim 판으로.
꾸러미는 {알려줄것['라이브러리']}
시작 명령은 {알려줄것['시작 명령']}
{알려줄것['여는 포트']} 포트를 연다

___
___
'''
print(프롬프트)""",
       answer="""프롬프트 = f'''Dockerfile 을 만들어 줘.

{알려줄것['언어와 버전']} 을 쓴다. 바탕 이미지는 slim 판으로.
꾸러미는 {알려줄것['라이브러리']}
시작 명령은 {알려줄것['시작 명령']}
{알려줄것['여는 포트']} 포트를 연다

앱은 127.0.0.1 이 아니라 0.0.0.0 으로 열게 한다
키는 환경변수로 받기만 한다. 값은 적지 마라
'''
print(프롬프트)""",
       check="""assert '0.0.0.0' in 프롬프트, '여는 주소를 못 박아야 한다'
assert '값은 적지' in 프롬프트 or '값을 적지' in 프롬프트, '키 값을 적지 말라고 해야 한다'
print()
print('두 줄이 들어갔다. 이 프롬프트를 그대로 Codex 에 붙여 넣는다.')"""),

    md("**왜 이 두 줄인가.**\n\n"
       "`0.0.0.0` &mdash; 안 적으면 상자는 뜨는데 밖에서 못 붙는다. 제일 잦은 사고다.\n\n"
       "`값은 적지 마라` &mdash; 안 적으면 키를 `ENV` 로 이미지에 박아 넣는다. 지워도 남는다."),

    md("## 4. 틀린 Dockerfile 찾기"),
    md("Codex 가 내놓은 것을 **그냥 쓰지 않는다.** 아래 셋을 차례로 본다."),

    prep("""# 검토할 Dockerfile 셋. 일부러 틀린 곳을 넣어 두었다.
후보 = [
    '바탕 이미지에 버전을 안 적었다',
    '키 값을 이미지에 박아 넣었다',
    '앱이 127.0.0.1 로 열려 밖에서 못 붙는다',
    '폴더를 통째로 복사해 잡동사니가 들어간다',
    '꾸러미를 코드보다 나중에 깔아 빌드가 느리다',
    '데이터를 이미지에 넣어 상자를 지우면 사라진다',
    '틀린 곳이 없다',
]
for i, x in enumerate(후보, 1):
    print('%d. %s' % (i, x))"""),

    prep("""D1 = '''
FROM python:latest
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ENV NVIDIA_API_KEY=nvapi-abc123
EXPOSE 8000
CMD ["python", "app.py"]
'''
print(D1)"""),

    Ex(2, "위 `D1` 에서 틀린 곳을 **넷** 고른다. 번호로 적는다.\n"
          "> 후보 목록에서 고른다. 순서는 상관없다.",
       setup="# 후보 번호를 넣는다",
       blank="답1 = [___, ___, ___, ___]",
       answer="답1 = [1, 2, 4, 5]",
       check="""정답 = {1, 2, 4, 5}
assert set(답1) == 정답, '다시 본다. 힌트 — latest · ENV · COPY . . · pip 순서'
for n in sorted(답1):
    print('%d. %s' % (n, 후보[n-1]))
print()
print('넷 다 찾았다. 이 넷이 실제로 제일 자주 나온다.')"""),

    prep("""D2 = '''
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY cell_process.csv .
EXPOSE 8000
CMD ["python", "app.py"]
'''
print(D2)"""),

    Ex(3, "`D2` 는 앞의 것보다 낫다. 그래도 **하나**가 남았다.\n"
          "> 순서도 맞고 키도 없다. 무엇이 걸리나.",
       setup="# 후보 번호 하나",
       blank="답2 = [___]",
       answer="답2 = [6]",
       check="""assert set(답2) == {6}, '데이터를 어디에 두었나 다시 본다'
print(후보[답2[0]-1])
print()
print('CSV 를 이미지에 넣었다. 데이터가 바뀔 때마다 이미지를 다시 만들어야 하고,')
print('상자를 지우면 안에 쌓인 것이 같이 사라진다. 밖에서 물려야 한다.')"""),

    md("**여기서 한 가지 더.** `D2` 는 앱이 `0.0.0.0` 으로 여는지 **Dockerfile 만 봐서는 모른다.**\n"
       "그건 `app.py` 안에 있다. 그래서 프롬프트에 미리 못 박아 두는 것이다."),

    md("## 5. compose.yml 읽기"),
    md("서비스가 여럿이면 **무엇이 밖으로 열리는지**가 제일 중요하다."),

    prep("""C1 = '''
services:
  web:
    build: ./web
    ports: ["3000:3000"]
    environment:
      API_URL: http://api:8000

  api:
    build: ./api
    ports: ["8000:8000"]

  db:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_PASSWORD: mypassword
'''
print(C1)"""),

    Ex(4, "`C1` 에서 **밖으로 열지 않아야 하는 서비스**를 고르고, 그 까닭을 한 줄 적는다.\n"
          "> `web` 은 사람이 브라우저로 쓴다. 나머지 둘은 누가 쓰나.",
       setup="# 서비스 이름과 까닭",
       blank="""닫아야할것 = '___'
까닭 = '___'
print(닫아야할것, '—', 까닭)""",
       answer="""닫아야할것 = 'db'
까닭 = '사람이 직접 쓰지 않는다. web 과 api 만 부르면 되니 안에서만 열면 된다'
print(닫아야할것, '—', 까닭)""",
       check="""assert 닫아야할것 == 'db', 'ports 를 열 이유가 없는 것을 고른다'
assert '___' not in 까닭, '까닭을 적는다'
print()
print('ports 를 지우면 같은 compose 안의 web · api 만 붙는다.')
print('한 가지 더 — POSTGRES_PASSWORD 를 파일에 그대로 적었다. .env 로 빼야 한다.')"""),

    md("## 6. 폐쇄망용으로 고치기"),
    md("바깥이 막힌 곳으로 넘길 때는 **`compose.yml` 을 따로 만든다.**\n"
       "`build:` 를 그대로 두면 받는 쪽에서 다시 만들려고 인터넷을 찾는다."),

    Ex(5, "`C1` 을 폐쇄망용으로 고친다. **`build:` 를 `image:` 로** 바꾼다.\n"
          "> 이미지 이름은 영문 소문자로 짓는다. 한글은 빌드에서 거절당한다.",
       setup="C2 = C1",
       blank="""C2 = C2.replace('build: ./web', 'image: ___')
C2 = C2.replace('build: ./api', 'image: ___')
print(C2)""",
       answer="""C2 = C2.replace('build: ./web', 'image: posco-web:1.0')
C2 = C2.replace('build: ./api', 'image: posco-api:1.0')
print(C2)""",
       check="""assert 'build:' not in C2, 'build 가 남아 있으면 받는 쪽이 다시 만들려 한다'
assert '___' not in C2, '이미지 이름을 채운다'
import re
for name in re.findall(r'image: (\\S+)', C2):
    assert re.match(r'^[a-z0-9._/-]+(:[a-zA-Z0-9._-]+)?$', name), '이름은 영문 소문자로: ' + name
print()
print('build 가 없어졌다. 이제 load 한 이미지로만 뜬다.')"""),

    md("## 7. 터미널에서 할 것"),
    md("여기까지가 노트북에서 하는 일이다. **아래는 터미널에서 친다.**\n"
       "노트북에서는 안 돌아가니 눈으로 읽고 순서만 익혀 둔다."),

    md("**만드는 쪽**\n\n"
       "```bash\n"
       "# 4단계 · 이미지를 만든다\n"
       "docker compose build\n"
       "docker images                        # posco-web · posco-api 가 보이나\n"
       "\n"
       "# 5단계 · 띄워서 확인한다\n"
       "docker compose up -d\n"
       "docker compose ps                    # 둘 다 Up 인가\n"
       "curl http://127.0.0.1:3000/          # 화면이 나오나\n"
       "```"),

    md("**옮기는 쪽**\n\n"
       "```bash\n"
       "# 6단계 · 파일 하나로 뽑는다\n"
       "docker save posco-web:1.0 posco-api:1.0 -o images.tar\n"
       "ls -lh images.tar                    # 100MB 안팎이면 정상\n"
       "\n"
       "# 7단계 · 옮긴 곳에서 띄운다 (인터넷 안 씀)\n"
       "docker load -i images.tar\n"
       "docker compose up -d\n"
       "```"),

    md("**막히면 보는 순서**\n\n"
       "```bash\n"
       "docker compose ps                    # 떴나\n"
       "docker compose logs web --tail 20    # 왜 안 되나\n"
       "lsof -nP -iTCP:3000 -sTCP:LISTEN     # 포트를 누가 쥐고 있나\n"
       "```"),

    Task(2, "**옮길 것 목록**을 만든다. 다른 조 PC 에서 띄우려면 무엇을 넘겨야 하나.\n"
            "> 넘기지 말아야 할 것도 같이 적는다.",
         blank="""넘길것 = ['___', '___', '___']
안넘길것 = ['___', '___']
print('넘긴다   :', ' · '.join(넘길것))
print('안 넘긴다 :', ' · '.join(안넘길것))""",
         answer="""넘길것 = ['images.tar', 'compose.yml', 'env.example']
안넘길것 = ['.env', 'node_modules 나 venv 폴더']
print('넘긴다   :', ' · '.join(넘길것))
print('안 넘긴다 :', ' · '.join(안넘길것))""",
         check="""assert '___' not in str(넘길것) + str(안넘길것), '다 채운다'
assert any('.env' in x for x in 안넘길것), '키가 든 파일은 안 넘긴다'
print()
print('소스 코드도 안 넘겨도 된다. 이미지 안에 이미 들어 있다.')"""),

    md("### 오늘 손에 남는 것\n\n"
       "**하나** &mdash; Codex 에게 시키기 전에 **여섯 가지**을 정한다. 안 주면 지어낸다.\n\n"
       "**둘** &mdash; 프롬프트에 **`0.0.0.0`** 과 **「값은 적지 마라」** 두 줄을 반드시 넣는다.\n\n"
       "**셋** &mdash; 받은 Dockerfile 은 **버전 · 키 · COPY 범위 · 순서** 넷을 본다.\n\n"
       "**넷** &mdash; `compose.yml` 에서 <b>ports 를 적은 것만</b> 밖으로 열린다. DB 에는 안 적는다.\n\n"
       "**다섯** &mdash; 폐쇄망용은 **`build:` 를 `image:` 로** 바꾼 파일을 따로 둔다.\n\n"
       "**여섯** &mdash; 넘길 것은 **`images.tar` · `compose.yml` · `env.example`** 셋이다."),
]

MODES = {("ex", 1): "together", ("ex", 2): "together", ("ex", 3): "solo",
         ("ex", 4): "solo", ("ex", 5): "solo",
         ("task", 1): "team", ("task", 2): "team"}

SPEC = ("Docker 다루기",
        "Codex 에게 시킬 것을 정하고, 받은 파일을 읽고 고친다", CELLS, MODES)
