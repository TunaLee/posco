"""3주차 D5 — MCP · 도구를 붙이는 규약"""
from nbkit import md, code, h, lab, prep, Ex, Task

BASE = 'https://tunalee.github.io/posco/data/'

CELLS = [
    md("## 1. 준비"),
    md("어제 만든 도구 넷은 **노트북 안에서만** 쓸 수 있었다.\n"
       "오늘은 같은 함수를 **MCP 서버**로 내보낸다. 그러면 Codex 에서도 사내 챗봇에서도 같은 것을 쓴다.\n\n"
       "> 서버는 보통 따로 도는 프로그램이지만, 여기서는 **노트북 안에서 서버를 만들고 바로 붙는다.**\n"
       "> 붙는 방식만 다를 뿐 주고받는 말은 같다."),

    prep("""# FastMCP 를 받는다. 서버를 짜는 데 드는 배선을 다 숨겨 준다.
!pip install -q fastmcp

import asyncio, pandas as pd
from fastmcp import FastMCP, Client

df = pd.read_csv('%scell_process.csv')
print('%%d행 %%d열' %% df.shape)""" % BASE),

    prep("""# 서버를 하나 만든다. 이름은 목록에 그대로 보인다.
mcp = FastMCP('공정 도우미')
print(mcp.name)"""),

    md("## 2. 첫 Tool"),
    md("함수 위에 **데코레이터 한 줄**을 얹으면 도구가 된다.\n"
       "타입힌트가 스키마가 되고, 따옴표 안 설명이 모델이 읽는 글이 된다."),

    prep("""# 어제 만든 불량률 조회를 그대로 옮긴다
@mcp.tool()
def defect_rate(machine: str, shift: str = '') -> str:
    '''설비호기의 불량률을 돌려준다. 교대조를 주면 그 안에서만 센다.

    machine: 설비호기. 1호기 ~ 4호기
    shift:   교대조. 주간 또는 야간. 비우면 전체
    '''
    if machine not in sorted(df['설비호기'].unique()):
        return '없는 설비다. 쓸 수 있는 이름: ' + ', '.join(sorted(df['설비호기'].unique()))
    d = df[df['설비호기'] == machine]
    if shift:
        d = d[d['교대조'] == shift]
    if not len(d):
        return '해당 조건에 데이터가 없다'
    bad = int((d['판정'] == '불량').sum())
    return '%s %s · 측정 %d건 중 불량 %d건 · 불량률 %.1f%%' % (
        machine, shift or '전체', len(d), bad, 100.0 * bad / len(d))"""),

    md("**어제 코드에서 바뀐 것은 데코레이터 한 줄과 타입 표시뿐이다.** 몸통은 그대로다."),

    md("### 서버에 무엇이 있는지 물어본다"),
    md("클라이언트를 붙여 `tools/list` 를 보낸다. 붙는 앱이 처음에 하는 일이 이것이다."),

    prep("""# 노트북 안에서 서버에 바로 붙는다
async def show_tools():
    async with Client(mcp) as c:
        for t in await c.list_tools():
            print('이름   %s' % t.name)
            print('설명   %s' % t.description.split('\\\\n')[0])
            print('인자   %s' % list(t.inputSchema['properties']))

await show_tools()"""),

    md("**손으로 적은 JSON 이 하나도 없다.** 어제 스무 줄 넘게 쓰던 도구 설명서가\n"
       "타입힌트와 설명에서 저절로 만들어졌다."),

    md("### 불러 본다"),

    prep("""# tools/call 을 보낸다
async def call(name, args):
    async with Client(mcp) as c:
        r = await c.call_tool(name, args)
        return r.content[0].text

print(await call('defect_rate', {'machine': '3호기', 'shift': '야간'}))
print(await call('defect_rate', {'machine': '3호기'}))"""),

    Ex(1, "**없는 설비**를 넣어 본다. 어제와 같은 친절한 답이 오는지 본다.\n"
          "> 서버가 예외로 죽으면 붙어 있는 앱이 전부 곤란해진다.",
       setup="# 1호기 ~ 4호기 말고 다른 것을 넣는다",
       blank="MACHINE = '___'",
       answer="MACHINE = '9호기'",
       check="print(await call('defect_rate', {'machine': MACHINE}))"),

    md("## 3. Resource — 주소로 여는 자료"),
    md("도구가 **버튼**이라면 리소스는 **서랍 속 문서**다.\n"
       "주소를 대면 그 내용이 오고, 두 번 읽어도 같다."),

    prep("""# 설비 제원을 주소로 연다. {name} 이 그대로 함수 인자가 된다.
@mcp.resource('machine://{name}/spec')
def machine_spec(name: str) -> str:
    '''설비 한 대의 제원과 담당 팀을 돌려준다'''
    d = df[df['설비호기'] == name]
    if not len(d):
        return '그런 설비가 없다'
    return '%s · 기록 %d건 · 교대조 %s · 첫 기록 %s' % (
        name, len(d), ' '.join(sorted(d['교대조'].unique())), d['시각'].min())"""),

    prep("""# 주소를 대고 읽는다
async def read(uri):
    async with Client(mcp) as c:
        r = await c.read_resource(uri)
        return r[0].text

print(await read('machine://3호기/spec'))
print(await read('machine://1호기/spec'))"""),

    md("**같은 주소를 두 번 읽어도 같은 것이 온다.** 아무것도 안 바뀐다.\n"
       "이게 Tool 과 갈리는 자리다 — 찾거나 계산하거나 바꾸면 Tool 이다."),

    Ex(2, "리소스를 하나 더 만든다. **교대조별 불량률**을 주소로 연다.\n"
          "> 주소 모양만 정하면 된다. 몸통은 위 함수를 참고한다.",
       setup="# 어떤 주소로 열지 정한다",
       blank="URI = 'shift://{name}/___'",
       answer="URI = 'shift://{name}/defect'",
       check="""print('정한 주소:', URI)
assert '___' not in URI, '주소를 채운다'
print('예: ' + URI.replace('{name}', '주간'))"""),

    md("## 4. 모델에게 넘긴다"),
    md("여기까지는 사람이 손으로 불렀다. 이제 **모델이 고르게** 한다.\n"
       "서버에서 받은 목록을 그대로 모델에 넘기면 된다."),

    prep("""# 어제 쓰던 키를 그대로 쓴다
import getpass, json, urllib.request
KEY = getpass.getpass('nvapi- 로 시작하는 키: ')

URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
MODEL = 'nvidia/llama-3.3-nemotron-super-49b-v1'

def chat(messages, tools=None, n=600):
    body = {'model': MODEL, 'max_tokens': n, 'temperature': 0, 'messages': messages}
    if tools:
        body['tools'] = tools
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        'Authorization': 'Bearer ' + KEY,
        'Content-Type': 'application/json', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as f:
        return json.load(f)['choices'][0]['message']"""),

    prep("""# MCP 도구 목록을 모델이 읽는 형식으로 바꾼다
async def as_tools():
    async with Client(mcp) as c:
        return [{'type': 'function',
                 'function': {'name': t.name,
                              'description': t.description,
                              'parameters': t.inputSchema}}
                for t in await c.list_tools()]

TOOLS = await as_tools()
print('넘길 도구 %d개' % len(TOOLS))"""),

    md("**이 한 함수가 MCP 와 모델을 잇는 전부다.** 이름·설명·스키마를 옮겨 담을 뿐이다."),

    prep("""# 판단은 모델이, 실행은 MCP 가 한다
async def run(question):
    messages = [{'role': 'system', 'content':
                 '너는 공정 데이터를 보는 비서다. 한국어로만 답한다. '
                 '숫자는 도구로 조회한 값만 쓴다.'},
                {'role': 'user', 'content': question}]
    for _ in range(4):
        m = chat(messages, TOOLS)
        messages.append(m)
        calls = m.get('tool_calls') or []
        if not calls:
            return (m.get('content') or '').strip() or '[답 없음]'
        for c in calls:
            args = json.loads(c['function']['arguments'] or '{}')
            print('  [MCP] %s(%s)' % (c['function']['name'], args))
            out = await call(c['function']['name'], args)
            messages.append({'role': 'tool', 'tool_call_id': c['id'], 'content': out})
    return '[한도]'"""),

    code("""# 물어본다
print(await run('3호기 야간조 불량률이 얼마야'))"""),

    md("**모델이 `defect_rate` 를 골라 불렀다.** 어제와 답은 같은데 경로가 달라졌다.\n\n"
       "어제 &mdash; 함수가 노트북 안에 있고 설명서를 손으로 썼다.\n"
       "오늘 &mdash; 함수가 **서버에** 있고 설명서는 **서버가 준다**.\n\n"
       "이 서버를 파일로 떼어 내면 Codex 도 Claude Desktop 도 같은 것을 쓴다."),

    Ex(3, "도구를 **하나 더** 붙이고 모델이 그것도 고르는지 본다.\n"
          "> 설비 목록을 돌려주는 도구다. 이름과 설명만 채운다.",
       setup="""@mcp.tool()
def machine_list() -> str:""",
       blank="""    '''___'''
    return ', '.join(sorted(df['설비호기'].unique()))""",
       answer="""    '''쓸 수 있는 설비호기 이름을 모두 돌려준다'''
    return ', '.join(sorted(df['설비호기'].unique()))""",
       check="""TOOLS = await as_tools()
print('도구 %d개' % len(TOOLS))
print(await run('어떤 설비가 있는지 알려줘'))"""),

    md("## 5. 파일로 떼어 내기"),
    md("노트북에서 확인했으면 **파일 하나로** 옮긴다. 그 파일이 곧 서버다."),

    prep("""# 지금까지 만든 것을 server.py 로 쓴다
SERVER = '''from fastmcp import FastMCP
import pandas as pd

df = pd.read_csv('cell_process.csv')
mcp = FastMCP('공정 도우미')

@mcp.tool()
def defect_rate(machine: str, shift: str = '') -> str:
    "설비호기의 불량률을 돌려준다. 교대조를 주면 그 안에서만 센다."
    d = df[df['설비호기'] == machine]
    if shift:
        d = d[d['교대조'] == shift]
    if not len(d):
        return '해당 조건에 데이터가 없다'
    bad = int((d['판정'] == '불량').sum())
    return '%s %s · 측정 %d건 중 불량 %d건' % (machine, shift or '전체', len(d), bad)

if __name__ == '__main__':
    mcp.run()
'''
open('server.py', 'w').write(SERVER)
print(SERVER[:200])"""),

    md("### 앱에 붙이는 설정"),
    md("이 파일을 가리키는 설정 한 장이면 붙는다. **앱 코드는 안 고친다.**"),

    prep("""# Claude Desktop · Codex 같은 앱의 설정 파일에 넣을 것
CONF = {
  'mcpServers': {
    '공정도우미': {
      'command': 'python',
      'args': ['/절대/경로/server.py']
    }
  }
}
print(json.dumps(CONF, ensure_ascii=False, indent=2))"""),

    md("> 경로는 **절대경로**로 적는다. 앱은 터미널 PATH 를 물려받지 않아서\n"
       "> 상대경로로 적으면 「서버를 못 찾는다」가 가장 흔한 사고다."),

    Task(1, "**우리 팀에 붙일 서버**를 설계한다. 코드는 안 쓴다. 네 칸만 채운다.\n"
            "> 2~3명이 한 조로 상의한다. 지금 손으로 하고 있는 일에서 고른다.",
         blank="""MY_SERVER = {
    '이름':        '___',
    '지금 손으로':   '___',
    'Resource':  ['___'],
    'Tool':      ['___'],
}
for k, v in MY_SERVER.items():
    print('%-10s %s' % (k, v if isinstance(v, str) else ' / '.join(v)))""",
         answer="""MY_SERVER = {
    '이름':        '점검 도우미',
    '지금 손으로':   '점검 때마다 작업표준을 폴더에서 찾고 이전 기록을 엑셀에서 본다',
    'Resource':  ['작업표준 전문', '설비 제원'],
    'Tool':      ['최근 점검 이력 조회', '규정 검색'],
}
for k, v in MY_SERVER.items():
    print('%-10s %s' % (k, v if isinstance(v, str) else ' / '.join(v)))""",
         check="""assert '___' not in str(MY_SERVER), '네 칸을 채운다'
print()
print('읽기만 하면 Resource, 찾거나 계산하면 Tool 이다')"""),

    md("### 오늘 손에 남는 것\n\n"
       "**하나** &mdash; 데코레이터 한 줄이면 함수가 도구가 된다. 몸통은 안 고친다.\n\n"
       "**둘** &mdash; 손으로 쓰던 도구 설명서가 **타입힌트와 설명**에서 만들어진다.\n\n"
       "**셋** &mdash; 주소로 읽는 것은 Resource, 찾거나 계산하는 것은 Tool 이다.\n\n"
       "**넷** &mdash; MCP 목록을 모델 형식으로 옮기는 함수 하나가 둘을 잇는다.\n\n"
       "**다섯** &mdash; 파일로 떼어 내면 **설정 한 장**으로 어느 앱에나 붙는다."),
]

MODES = {("ex", 1): "together", ("ex", 2): "solo", ("ex", 3): "solo",
         ("task", 1): "team"}

SPEC = ("MCP — 도구를 붙이는 규약",
        "어제 만든 함수를 서버로 내보내고, 모델이 그것을 부르게 한다", CELLS, MODES)
