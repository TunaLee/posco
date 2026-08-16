"""사내 도우미 호스트.

teams/ 안의 파일을 모두 MCP 서버로 붙이고, 채팅창에서 물으면
모델이 그 도구들 중에 골라 부른다.

    NVIDIA_API_KEY=nvapi-... python host.py

붙는 규칙 — teams/team1.py 의 도구 defect_rate 는 team1_defect_rate 가 된다.
접두어를 안 붙이면 같은 이름의 도구가 서로를 덮는다.
"""
import glob
import json
import os
import pathlib
import urllib.request
from urllib.parse import urlparse

from fastmcp import Client, FastMCP
from fastmcp.server import create_proxy
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

HERE = pathlib.Path(__file__).parent
KEY = os.environ.get('NVIDIA_API_KEY', '')
URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
MODEL = 'nvidia/llama-3.3-nemotron-super-49b-v1'

SYSTEM = ('너는 공정 데이터를 보는 사내 비서다. 한국어로만 답한다. '
          '숫자는 도구로 조회한 값만 쓴다. 도구가 없는 것은 모른다고 답한다.')

# ── 조별 서버를 붙인다 ──────────────────────────────────────────────
# 두 가지 길이 있다.
#   TEAM_URLS 가 있으면  주소로 붙는다 (compose 로 띄웠을 때)
#   없으면               teams/ 의 파일을 직접 띄워 붙는다 (한 대에서 돌릴 때)
host = FastMCP('사내 도우미')
TEAMS = []

for url in [u.strip() for u in os.environ.get('TEAM_URLS', '').split(',') if u.strip()]:
    name = urlparse(url).hostname or url          # http://team1:8000/mcp → team1
    host.mount(create_proxy(url), namespace=name)
    TEAMS.append(name)

if not TEAMS:
    ROOT = HERE.parent                              # mcp-host/
    found = (sorted(glob.glob(str(ROOT / 'teams' / '*' / 'server.py')))   # teams/team1/server.py
             + sorted(glob.glob(str(ROOT / 'teams' / '*.py'))))          # teams/team1.py
    for path in found:
        p = pathlib.Path(path)
        name = p.parent.name if p.name == 'server.py' else p.stem
        host.mount(create_proxy(path), namespace=name)
        TEAMS.append(name)


def chat(messages, tools=None, n=600):
    body = {'model': MODEL, 'max_tokens': n, 'temperature': 0, 'messages': messages}
    if tools:
        body['tools'] = tools
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        'Authorization': 'Bearer ' + KEY,
        'Content-Type': 'application/json', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as f:
        return json.load(f)['choices'][0]['message']


def to_openai(tools):
    return [{'type': 'function',
             'function': {'name': t.name,
                          'description': t.description,
                          'parameters': t.inputSchema}}
            for t in tools]


def split(name):
    """team1_defect_rate → ('team1', 'defect_rate')"""
    for t in TEAMS:
        if name.startswith(t + '_'):
            return t, name[len(t) + 1:]
    return '', name


async def run(question):
    """day12 에서 만든 것과 같은 고리다. 서버가 여럿일 뿐이다."""
    called = []
    seen = {}                       # 같은 도구를 같은 인자로 또 부르는 것을 막는다
    async with Client(host) as client:
        spec = to_openai(await client.list_tools())
        messages = [{'role': 'system', 'content': SYSTEM},
                    {'role': 'user', 'content': question}]
        for _ in range(5):
            m = chat(messages, spec)
            messages.append(m)
            calls = m.get('tool_calls') or []
            if not calls:
                text = (m.get('content') or '').strip()
                return text or '붙어 있는 도구로는 답할 수 없다', called
            for c in calls:
                name = c['function']['name']
                args = json.loads(c['function']['arguments'] or '{}')
                team, tool = split(name)
                key = name + json.dumps(args, sort_keys=True, ensure_ascii=False)
                if key in seen:
                    # 답이 마음에 안 들어도 같은 것을 또 부르면 결과는 같다.
                    # 그대로 두면 한도까지 맴돈다.
                    out = ('이미 부른 도구다. 결과는 아래와 같았다. '
                           '다시 부르지 말고 이것으로 답하라.\n' + seen[key])
                else:
                    try:
                        out = (await client.call_tool(name, args)).content[0].text
                    except Exception as e:                 # 한 조가 터져도 나머지는 산다
                        out = '도구가 실패했다: %s' % e
                    seen[key] = out
                    called.append({'team': team, 'tool': tool, 'args': args, 'out': out})
                messages.append({'role': 'tool', 'tool_call_id': c['id'], 'content': out})
    return '[한도] 다섯 번 안에 못 끝냈다', called


async def page(request):
    return FileResponse(HERE / 'index.html')


async def tools(request):
    async with Client(host) as c:
        got = await c.list_tools()
    out = []
    for t in got:
        team, tool = split(t.name)
        out.append({'team': team, 'tool': tool,
                    'desc': (t.description or '').split('\n')[0]})
    return JSONResponse({'teams': TEAMS, 'tools': out})


async def ask(request):
    body = await request.json()
    question = (body.get('question') or '').strip()
    if not question:
        return JSONResponse({'error': '질문이 비었다'}, status_code=400)
    if not KEY:
        return JSONResponse({'error': 'NVIDIA_API_KEY 가 없다'}, status_code=500)
    try:
        answer, called = await run(question)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
    return JSONResponse({'answer': answer, 'called': called})


app = Starlette(routes=[Route('/', page),
                        Route('/tools', tools),
                        Route('/chat', ask, methods=['POST'])])

if __name__ == '__main__':
    import uvicorn
    print('붙은 조 —', ', '.join(TEAMS) or '없다. teams/ 에 .py 를 넣는다')
    uvicorn.run(app, host=os.environ.get('HOST_BIND', '127.0.0.1'),
                port=int(os.environ.get('PORT', '8000')))
