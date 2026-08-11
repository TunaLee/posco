"""3주차 D2 — 에이전트의 구조 · 도구를 붙여 루프를 돌린다"""
from nbkit import md, code, h, lab, prep, Ex, Task

CELLS = [
    md("## 1. 준비"),
    md("오늘 만드는 것은 **설비 일지를 대신 찾아 주는 비서**다.\n\n"
       "「3호기 어제 불량률이 2 퍼센트 넘었어?」 처럼 물으면, 모델이 스스로 사내 기록을 조회하고\n"
       "필요하면 계산까지 해서 답한다. 끝까지 가면 도구를 하나 더 붙이는 데 **세 줄**이면 된다."),
    md("어제 쓰던 `build.nvidia.com` 키를 그대로 쓴다.\n\n"
       "1. `build.nvidia.com` 에 접속해 로그인한다\n"
       "2. 아무 모델이나 열고 **Get API Key** 를 누른다\n"
       "3. `nvapi-` 로 시작하는 키를 복사해 아래 셀을 실행한 뒤 입력창에 붙여 넣는다"),

    prep("""# 키는 화면에 안 찍히게 받는다. 붙여 넣고 Enter 를 누르면 된다.
import getpass, json, urllib.request
KEY = getpass.getpass('nvapi- 로 시작하는 키: ')
print('키 길이', len(KEY))     # 60~80 정도면 제대로 들어간 것이다"""),

    prep("""# 모델에 대화를 통째로 보내는 함수. 실패해도 노트북이 멈추지 않게 [실패] 를 돌려준다.
URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
MODEL = 'nvidia/llama-3.3-nemotron-super-49b-v1'

def chat(messages, tools=None, n=400, temp=0):
    body = {'model': MODEL, 'max_tokens': n, 'temperature': temp,
            'messages': messages}
    if tools:                       # 도구 목록은 있을 때만 같이 보낸다
        body['tools'] = tools
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        'Authorization': 'Bearer ' + KEY,
        'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as f:
            return json.load(f)['choices'][0]['message']
    except Exception as e:
        return {'role': 'assistant', 'content': '[실패] %s' % str(e)[:80]}"""),

    prep("""# 한 문장만 물어볼 때 쓰는 짧은 이름
def say(text, n=200):
    return (chat([{'role': 'user', 'content': text}], n=n).get('content') or '').strip()

print(say('한 단어로만 답하라. 대한민국의 수도는?', 10))   # '서울' 이 나오면 준비 끝이다"""),

    md("> `[실패]` 가 나오면 키를 잘못 붙였거나 모델이 붐비는 것이다. 셀을 다시 실행해 본다."),

    md("## 2. 도구 없이 물어보면"),
    md("먼저 **모델 혼자서는 어디까지 되는지** 본다. 성격이 다른 세 가지를 물어본다."),

    code("""# 세 가지를 그냥 물어본다
for q in ['17 곱하기 24 는 얼마인가? 숫자만 답하라.',
          '오늘 날짜는? 날짜만 답하라.',
          '3호기의 어제 불량률은 몇 퍼센트인가?']:
    print('Q', q)
    print('A', say(q, 60).replace('\\n', ' ')[:100])
    print()"""),

    md("세 답이 전부 다르게 나온다.\n\n"
       "| 질문 | 이 모델은 | 왜 |\n|---|---|---|\n"
       "| 17 × 24 | **맞힌다** | 이 크기면 두 자리는 된다. 자릿수를 키우면 갈린다 |\n"
       "| 오늘 날짜 | **옛날 날짜**를 자신 있게 답한다 | 학습이 끝난 시점에 멈춰 있다 |\n"
       "| 3호기 불량률 | **되묻는다** | 사내 기록이라 배운 적이 없다 |\n\n"
       "가운데가 제일 위험하다. **틀린 답이 맞는 답과 똑같은 말투로 나온다.**\n"
       "셋 다 원인은 하나다 &mdash; 모델 안에 그 답이 없다."),

    md("## 3. 계산 하나는 프롬프트로도 나아진다"),
    md("도구로 넘어가기 전에, **프롬프트만으로 어디까지 되는지** 먼저 본다.\n"
       "한 줄씩 쓰게 하면 어려운 곱셈이 쉬운 덧셈으로 갈린다.\n"
       "두 자리 곱셈은 이 크기 모델이면 그냥도 맞힌다. 갈리는 자리는 그 다음이다."),

    code("""# 그냥 물었을 때와 자리별로 나누게 했을 때
print('[그냥]      ', say('17 곱하기 24 는? 숫자만 답하라.', 30).replace('\\n', ' '))
print('[자리별로]  ', say('17 곱하기 24 를 자리별로 나눠 한 줄씩 계산하고 마지막 줄에 답만 써라.', 200)
      .replace('\\n', ' / ')[:160])"""),

    Ex(1, "곱하는 두 수를 **네 자리 × 세 자리**로 키워 다시 돌려 본다.\n"
          "> `___` 자리에 `4271 곱하기 386` 처럼 넣으면 된다. 아래 `check` 가 정답을 같이 찍어 준다.",
       setup="# 자릿수를 키우면 같은 방법이 계속 통하는지 보는 것이다",
       blank="q = '___ 를 자리별로 나눠 한 줄씩 계산하고 마지막 줄에 답만 써라.'",
       answer="q = '4271 곱하기 386 을 자리별로 나눠 한 줄씩 계산하고 마지막 줄에 답만 써라.'",
       check="print(say(q, 300))\nprint('정답', 4271 * 386)"),

    md("**단계를 다 펼쳐 놓고도 마지막 합에서 틀린다.** 중간 줄이 그럴듯해서 더 안 보인다.\n"
       "맞았는지 확인할 방법이 없다는 것이 더 곤란하다. 정확한 값은 **계산기에 넘긴다**."),

    md("## 4. 도구를 만들어 준다"),
    md("도구는 특별한 것이 아니다. **평범한 파이썬 함수**다.\n"
       "지금은 사내 기록 대신 표 하나를 코드 안에 넣어 두고 쓴다. "
       "현업에서는 이 자리에 사내 DB 조회나 엑셀 읽기가 들어간다."),

    prep("""# 어제 하루치 설비 일지 — 현업에서는 이 자리가 DB 조회나 엑셀 읽기가 된다
LOG = {
    '1호기': {'라인': 'A', '생산': 1240, '불량': 30, '근무조': '주간'},
    '2호기': {'라인': 'A', '생산':  980, '불량': 11, '근무조': '야간'},
    '3호기': {'라인': 'B', '생산': 1530, '불량': 28, '근무조': '주간'},
    '4호기': {'라인': 'B', '생산':  760, '불량': 24, '근무조': '야간'},
}
for k, v in LOG.items():
    print('%s  %s라인  생산 %5d  불량 %3d' % (k, v['라인'], v['생산'], v['불량']))"""),

    prep("""# 함수 셋 — 계산기 · 오늘 날짜 · 설비 조회
import datetime

def calc(expr):
    \"\"\"산술식 하나를 계산해 문자열로 돌려준다\"\"\"
    try:
        return str(eval(expr, {'__builtins__': {}}, {}))
    except Exception:                       # 죽지 말고 고칠 방법을 알려 준다
        return '계산할 수 없다. 숫자와 + - * / ( ) 만 넣어라. 예: 28/1530*100'

def today():
    \"\"\"오늘 날짜\"\"\"
    return datetime.date.today().isoformat()

def machine_info(machine):
    \"\"\"설비 한 대의 어제 기록. 없는 이름이면 쓸 수 있는 이름을 알려 준다.\"\"\"
    v = LOG.get(machine)
    if v is None:
        return '그런 설비는 없다. 쓸 수 있는 이름: ' + ', '.join(LOG)
    return '%s: %s라인, 생산 %d개, 불량 %d개, 근무조 %s' % (
        machine, v['라인'], v['생산'], v['불량'], v['근무조'])

FUNCS = {'calc': calc, 'today': today, 'machine_info': machine_info}
print(calc('17*24'))
print(today())
print(machine_info('3호기'))
print(machine_info('9호기'))     # 없는 이름을 넣으면 이렇게 알려 준다"""),

    md("모델은 이 함수를 **볼 수 없다**. 이름 · 설명 · 인자 모양만 글로 건네받는다.\n"
       "그 설명이 곧 모델용 프롬프트다. 애매하게 적으면 도구를 안 부르거나 엉뚱하게 부른다."),

    prep("""# 모델에게 건네는 도구 목록. spec() 은 매번 같은 모양을 찍어 주는 짧은 도우미다.
def spec(name, desc, props, required):
    return {'type': 'function', 'function': {
        'name': name, 'description': desc,
        'parameters': {'type': 'object', 'properties': props, 'required': required}}}

TOOLS = [
    spec('calc', '산술식을 계산한다. 나눗셈·퍼센트처럼 정확한 값이 필요할 때 쓴다.',
         {'expr': {'type': 'string', 'description': '파이썬 산술식. 예: 28/1530*100'}}, ['expr']),
    spec('today', '오늘 날짜를 YYYY-MM-DD 로 돌려준다.', {}, []),
    spec('machine_info', '설비 한 대의 어제 생산량·불량 수·라인·근무조를 사내 일지에서 찾아 돌려준다.',
         {'machine': {'type': 'string', 'description': '설비 이름. 예: 3호기'}}, ['machine']),
]
print(json.dumps(TOOLS[2], ensure_ascii=False, indent=1))"""),

    md("## 5. 모델이 도구를 고른다"),
    md("도구 목록을 같이 보내면 무엇이 달라지는지 본다."),

    code("""# 도구 목록을 같이 보내면 답 대신 '무엇을 부를지' 가 돌아온다
m = chat([{'role': 'user', 'content': '3호기 어제 불량률은?'}], TOOLS, 200)
print('내용     ', m.get('content'))
print('도구 호출', m.get('tool_calls'))"""),

    md("`content` 가 비고 `tool_calls` 가 찬다. **모델이 고른 것은 답이 아니라 도구**다.\n"
       "실제로 부르는 것은 우리 쪽 코드다. 결과를 다시 넣어 줘야 비로소 답이 나온다.\n\n"
       "> `tool_calls` 가 계속 `None` 이면 그 모델이 도구 호출을 안 받는 것이다.\n"
       "> 위 준비 셀의 `MODEL` 을 `meta/llama-3.3-70b-instruct` 로 바꿔 다시 실행한다."),

    md("## 6. 루프 — 판단 · 행동 · 관찰"),
    md("도구를 부르고, 결과를 되먹이고, 다시 묻는다. **더 부를 것이 없을 때까지** 도는 것이 에이전트다.\n"
       "아래가 그 전부다. 열 줄 남짓이고, 오늘 뒤에 나오는 것들은 전부 이 함수 주변에 붙는다."),

    prep("""# 에이전트 본체. 마지막 대화는 LAST 에 남겨 두었다가 9절에서 다시 본다.
SYSTEM = ('너는 공정 데이터 비서다. 필요하면 도구를 부르고, 모르면 모른다고 답한다. '
          '한국어로만 답한다.')   # 이 한 줄이 없으면 중국어 낱말이 섞여 나오기도 한다
LAST = []

def run_agent(question, system=SYSTEM, max_steps=5, log=True):
    global LAST
    messages = [{'role': 'system', 'content': system},
                {'role': 'user', 'content': question}]
    for step in range(max_steps):
        m = chat(messages, TOOLS, 500)           # ① 판단 — 부를까, 답할까
        messages.append(m)
        calls = m.get('tool_calls') or []
        if not calls:                            # 부를 것이 없으면 그것이 답이다
            LAST = messages
            return m.get('content') or ''
        for c in calls:                          # ② 행동 — 고른 도구를 실행
            name = c['function']['name']
            args = json.loads(c['function']['arguments'] or '{}')
            try:
                out = FUNCS[name](**args)
            except Exception as e:           # 에러도 결과처럼 되먹인다
                out = '오류: %s' % e
            if log:
                print('  [도구] %s(%s) -> %s' % (name, args, out))
            messages.append({'role': 'tool', 'tool_call_id': c['id'],
                             'content': out})    # ③ 관찰 — 결과를 대화에 되먹인다
    LAST = messages
    return '[한도] %d번 안에 못 끝냈다' % max_steps"""),

    code("""# 도구가 필요한 질문
print(run_agent('3호기 어제 불량률은 몇 퍼센트야?'))"""),

    md("`[도구]` 줄이 실제로 부른 기록이다. 조회로 숫자를 가져오고, 계산기로 퍼센트를 냈다면 두 줄이 찍힌다."),

    code("""# 도구가 필요 없는 질문 — [도구] 줄이 안 찍힌다
print(run_agent('안녕? 너는 무슨 일을 하니?'))"""),

    md("좋은 에이전트는 **도구를 안 쓸 때도 안다**. 상식 질문까지 도구를 부르면 느리고 비싸진다."),

    md("## 7. 멀티스텝 — 앞 결과가 있어야 다음을 부른다"),
    md("한 번에 안 끝나는 질문을 준다. 앞 도구의 결과를 봐야 다음 도구를 정할 수 있는 것들이다."),

    code("""# 조회 → 비교
print(run_agent('3호기 어제 불량률이 2 퍼센트보다 높았어?'))"""),

    md("`[도구]` 가 한 줄만 찍히기도 한다. 나눗셈이 쉬우면 **모델이 그냥 계산해 버린다**.\n"
       "그래도 **조회는 반드시 먼저** 한다 &mdash; 생산량과 불량 수는 지어낼 수가 없기 때문이다."),

    code("""# 조회 네 번 → 집계
print(run_agent('1호기부터 4호기까지 어제 불량률을 모두 구해서 가장 높은 설비를 알려줘'))"""),

    md("`[도구]` 줄이 **두 번 이상** 찍히면 멀티스텝이다. 앞 결과를 보고 다음 도구를 정했다는 뜻이다.\n"
       "이 부분이 「미리 순서를 정해 둔 코드」와 갈리는 지점이다."),

    Ex(2, "**없는 설비 이름**을 넣어 물어본다. 에이전트가 어떻게 빠져나오는지 본다.\n"
          "> 쓸 수 있는 이름은 1호기 · 2호기 · 3호기 · 4호기 뿐이다. `7호기` 처럼 없는 것을 넣어 본다.",
       setup="# 도구가 던지는 에러 문구가 다음 행동을 어떻게 바꾸는지 보는 것이다",
       blank="ans = run_agent('___ 의 어제 불량률을 알려줘')",
       answer="ans = run_agent('7호기의 어제 불량률을 알려줘')",
       check="print(ans)"),

    md("도구가 **쓸 수 있는 이름을 알려 주는 에러**를 돌려주면, 모델은 그걸 읽고 다시 고른다.\n"
       "`KeyError` 로 죽는 도구였다면 여기서 루프가 끝났을 것이다. **에러 문구가 곧 다음 행동의 힌트**다."),

    md("## 8. 안전장치"),
    md("루프는 스스로 멈추지 않을 수 있다. 그래서 **한도**를 같이 만든다.\n"
       "`max_steps` 를 줄이면 도중에 끊긴다는 것을 먼저 확인한다."),

    code("""# 한도를 1로 줄이면 도구를 한 번 부르고 끝난다
print(run_agent('1호기부터 4호기까지 평균 불량률을 알려줘', max_steps=1))"""),

    Ex(3, "위 질문이 **끝까지 가는 최소 한도**를 찾는다.\n"
          "> `2` 부터 하나씩 올려 가며 `[한도]` 가 안 뜨는 값을 찾는다.\n"
          "> 네 대를 한 번에 조회하고(1회) 그 결과로 답하니(2회) 두 번이면 된다.",
       setup="# 한도는 작으면 답이 안 나오고, 크면 비용이 샌다",
       blank="LIMIT = ___",
       answer="LIMIT = 2",
       check="print(run_agent('1호기부터 4호기까지 평균 불량률을 알려줘', max_steps=LIMIT))"),

    md("현업에서는 여기에 두 가지를 더 붙인다.\n"
       "**되돌릴 수 없는 도구**(삭제 · 발주 · 메일 발송)는 실행 전에 사람에게 묻고,\n"
       "**부른 도구와 인자를 전부 로그로 남긴다**. 안 보이면 못 고친다."),

    md("## 9. 컨텍스트 — 대화가 얼마나 커지는가"),
    md("모델은 지난 대화를 가지고 있지 않다. **매 호출마다 목록 전체를 다시 보낸다.**\n"
       "그래서 도구가 돌려준 것이 쌓이면 보내는 양이 계속 커진다. 방금 대화로 직접 세어 본다."),

    code("""# 방금 대화에 무엇이 들어 있는지 본다
for m in LAST:
    print('%-9s %s' % (m['role'], str(m.get('content'))[:70]))
print()
print('메시지 %d개 · 글자 %d자' % (len(LAST), len(json.dumps(LAST, ensure_ascii=False))))"""),

    code("""# 도구를 많이 부르는 질문일수록 커진다
run_agent('1호기부터 4호기까지 불량률을 모두 구해서 라인별로 정리해줘', log=False)
print('메시지 %d개 · 글자 %d자' % (len(LAST), len(json.dumps(LAST, ensure_ascii=False))))"""),

    md("늘어나는 것은 사람이 친 말이 아니라 **도구가 돌려준 것**이다. 줄일 자리도 거기다."),

    md("### 줄이는 법 — 요약해서 넘긴다"),

    prep("""# 대화를 글로 펼쳐 요약을 받는다
def flatten(messages):
    return '\\n'.join('%s: %s' % (m['role'], str(m.get('content'))[:200])
                     for m in messages)"""),

    code("""# 정한 것과 못 푼 것만 남긴다
brief = say('아래 대화를 세 줄로 요약하라. 정한 것과 아직 못 푼 것만 남기고 중복은 버려라.\\n\\n'
            + flatten(LAST), 300)
print(brief)
print()
print('원본 %d자 -> 요약 %d자' % (len(json.dumps(LAST, ensure_ascii=False)), len(brief)))"""),

    md("요약은 **되돌릴 수 없다**. 무엇을 남길지 미리 정해 두지 않으면 필요한 것부터 사라진다.\n"
       "그래서 실무에서는 「정한 것 · 못 푼 것 · 파일 경로」처럼 **남길 항목을 먼저 정해 두고** 요약시킨다."),

    md("## 10. 내 업무로"),
    md("여기서부터는 각자 자기 업무로 바꾼다. **루프 코드는 손대지 않는다.**\n"
       "바꾸는 것은 시스템 프롬프트 한 줄, 데이터, 도구 설명뿐이다."),

    Task(1, "`SYSTEM` 한 줄만 바꿔 답의 모양을 고정한다.\n"
            "> 「너는 무엇인가 · 언제 도구를 부르나 · 어떤 형식으로 답하나」 세 가지를 적는다.\n"
            "> 같은 질문에 답이 어떻게 달라지는지 앞 절과 견줘 본다.",
         blank="""MY_SYSTEM = '너는 ___ 다. ___ 할 때만 도구를 부르고, ___ 형식으로만 답한다.'
print(run_agent('3호기 어제 불량률 알려줘', system=MY_SYSTEM))""",
         answer="""MY_SYSTEM = ('너는 품질관리 담당자다. 숫자가 필요할 때만 도구를 부르고, '
             '「설비 / 불량률 / 판정」 세 줄로만 답한다. 기준은 2 퍼센트다.')
print(run_agent('3호기 어제 불량률 알려줘', system=MY_SYSTEM))""",
         check="print('같은 도구라도 시스템 프롬프트가 행동을 바꾼다')"),

    Task(2, "`LOG` 를 **자기 업무 데이터**로 바꾸고, 도구 설명도 그 말로 고친다.\n"
            "> 설비가 아니라 거래처 · 품목 · 창고 무엇이든 된다. 열 이름만 자기 말로 바꾸면 된다.\n"
            "> 설명을 애매하게 적으면 도구를 안 부르거나 엉뚱하게 부른다. 일부러 애매하게도 해 본다.",
         blank="""LOG = {
    '___': {'___': ___, '___': ___},
    '___': {'___': ___, '___': ___},
}
TOOLS[2]['function']['description'] = '___'
print(run_agent('___ 알려줘'))""",
         answer="""LOG = {
    'A거래처': {'발주': 320, '입고': 300, '지연일': 2},
    'B거래처': {'발주': 150, '입고': 150, '지연일': 0},
    'C거래처': {'발주': 480, '입고': 400, '지연일': 5},
}
TOOLS[2]['function']['description'] = '거래처 한 곳의 이번 달 발주·입고·지연일을 사내 기록에서 찾아 돌려준다.'
print(run_agent('C거래처 입고율이 90 퍼센트를 넘었는지 알려줘'))""",
         check="print('도구 설명은 모델용 프롬프트다 — 구체적일수록 잘 고른다')"),

    Task(3, "도구를 **하나 더** 붙인다. 함수 하나와 설명 하나면 루프는 그대로 돈다.\n"
            "> ① 파이썬 함수를 쓴다 → ② `FUNCS` 에 이름을 등록한다 → ③ `TOOLS` 에 설명을 넣는다.\n"
            "> 세 줄이 끝이다. `run_agent` 는 한 글자도 안 고친다.",
         blank="""def my_tool(___):
    return '___'

FUNCS['___'] = my_tool
TOOLS.append(spec('___', '___', {'___': {'type': 'string', 'description': '___'}}, ['___']))
print(run_agent('___'))""",
         answer="""def line_total(line):
    rows = [v for v in LOG.values() if v.get('라인') == line]
    if not rows:
        return '그런 라인은 없다. 쓸 수 있는 라인: A, B'
    return '%s라인 생산 %d개, 불량 %d개' % (line, sum(r['생산'] for r in rows),
                                        sum(r['불량'] for r in rows))

FUNCS['line_total'] = line_total
TOOLS.append(spec('line_total', '라인 하나의 어제 생산량과 불량 수를 합쳐 돌려준다.',
                  {'line': {'type': 'string', 'description': '라인 이름. 예: A'}}, ['line']))
print(run_agent('A라인과 B라인 중 어제 불량률이 높은 쪽은?'))""",
         check="print('루프는 한 줄도 안 고쳤다 — 도구 목록만 늘었다')"),

    md("**도구를 늘려도 루프는 그대로다.** 바뀌는 것은 목록과 설명뿐이다.\n"
       "그래서 에이전트를 키우는 일은 코드를 늘리는 일이 아니라 **도구를 정리하는 일**이 된다."),

    md("## 11. 반출본 만들기 — 컬럼 이름부터"),
    md("여기서부터는 **공정 데이터를 Codex 에 어떻게 넘기느냐**의 문제다.\n\n"
       "개인정보라면 이름·사번 같은 식별자만 떼면 됐다. 공정 데이터는 반대다.\n"
       "코팅 로딩, 전극 밀도, 화성 전압 — **그 숫자 자체가 레시피**라 뗄 식별자가 없다.\n"
       "그래서 값을 지우는 대신 **절대값을 안 넘기는 형태로 바꿔서** 넘긴다."),

    prep("""# 셀 공정 기록 2,400행을 읽어 온다. 난수로 만든 가상 데이터라 이 파일 자체는 반출 걱정이 없다.
import pandas as pd, numpy as np

URL = 'https://tunalee.github.io/posco/data/cell_process.csv'
df = pd.read_csv(URL, parse_dates=['시각'])
print(df.shape)
print(df.head(3).to_string(index=False))"""),

    md("### 이대로 붙이면 무엇이 나가나"),

    code("""# 값을 한 줄도 안 보내고 컬럼 이름만 보내도 이만큼이 나간다
print(list(df.columns))"""),

    md("`화성_3단계_CV_전압` 하나로 **화성 공정이 몇 단인지, 어느 단이 CV 구간인지**가 드러난다.\n"
       "`NMP_투입비` 는 슬러리 배합이고, `코팅_로딩_mg_cm2` 와 `전극_밀도` 는 셀 설계값이다.\n"
       "**값보다 컬럼명이 먼저 샌다.**"),

    code("""# 값도 마찬가지다 — 118.5 를 보면 건조로 온도대가, 3.48 을 보면 프레스 후 밀도가 그대로 보인다
print(df[['건조_ZONE2_TEMP', '코팅_로딩_mg_cm2', '전극_밀도', '화성_3단계_CV_전압']]
      .head(3).to_string(index=False))"""),

    code("""# 로트 번호와 시각도 값이다 — 순번 증가율에서 생산량이, 간격에서 tact time 이 나온다
print(df['로트번호'].head(2).tolist(), '...', df['로트번호'].tail(1).tolist())
print('로트 수', df['로트번호'].nunique())
print('가장 흔한 간격', df['시각'].diff().mode()[0])"""),

    md("### 내보내기 전에 표부터 손본다"),
    md("이 표에는 실제 라인에서 흔한 사고가 일부러 들어 있다. **반출본을 만들기 전에** 잡아 둔다.\n"
       "안 잡고 변환하면 평균과 표준편차가 오염돼서 반출본 전체가 틀어진다."),

    code("""# 어디에 무엇이 있는지 훑는다
print('결측       ', df.isna().sum()[lambda s: s > 0].to_dict())
run = df['프레스_1호기_압력'].groupby((df['프레스_1호기_압력'].diff() != 0).cumsum()).size()
print('같은 값 연속', run.max(), '행')
print('ZONE1 범위 ', df['건조_ZONE1_TEMP'].min(), '~', df['건조_ZONE1_TEMP'].max())
print('시각 역행  ', (df['시각'].diff().dt.total_seconds() < 0).sum(), '건')
print('시각 중복  ', df['시각'].duplicated().sum(), '건')"""),

    md("네 가지가 그대로 보인다.\n\n"
       "| 무엇 | 어디에 | 왜 생기나 |\n|---|---|---|\n"
       "| 연속 결측 40행 | `건조_ZONE2_TEMP` | 센서 단선 |\n"
       "| 같은 값 60행 | `프레스_1호기_압력` | 값 고착 — 센서가 멎었다 |\n"
       "| 최대 278.6 | `건조_ZONE1_TEMP` | 화씨가 섞여 들어왔다 |\n"
       "| 역행 3건 · 중복 15건 | `시각` | 수집기 재시작 |"),

    code("""# 화씨로 들어온 구간만 되돌린다. 섭씨 라인이 126~140 이라 150 을 넘으면 화씨로 본다.
mask = df['건조_ZONE1_TEMP'] > 150
df.loc[mask, '건조_ZONE1_TEMP'] = ((df.loc[mask, '건조_ZONE1_TEMP'] - 32) * 5 / 9).round(1)
print('되돌린 행', mask.sum(), '· 범위', df['건조_ZONE1_TEMP'].min(), '~', df['건조_ZONE1_TEMP'].max())"""),

    code("""# 고착 구간은 결측으로 돌린다. 그대로 두면 평균과 표준편차가 끌려간다.
same = df['프레스_1호기_압력'].diff() == 0
df.loc[same, '프레스_1호기_압력'] = np.nan
print('결측으로 돌린 행', same.sum())
df = df.sort_values('시각').drop_duplicates('시각').reset_index(drop=True)
print('정렬·중복 제거 후', len(df), '행')"""),

    md("### 이름 규칙 — 물리량은 남기고 공정 맥락은 지운다"),
    md("`FEAT_017` 처럼 다 지우면 모델이 **무슨 값인지 몰라** 코드 품질이 떨어진다.\n"
       "그래서 앞부분에 **물리량 종류**만 남기고, 뒷부분의 공정 이름을 순번으로 바꾼다.\n\n"
       "| 원본 | 익명명 | 살아 있는 정보 |\n|---|---|---|\n"
       "| 건조_ZONE2_TEMP | `TEMP_D2` | 온도끼리 같이 볼 만하다 |\n"
       "| 프레스_1호기_압력 | `PRES_B1` | 압력이다 |\n"
       "| 화성_3단계_CV_전압 | `VOLT_P3` | 전압이다 |\n"
       "| NMP_투입비 | `RATIO_M2` | 비율이라 합이 1일 수 있다 |"),

    prep("""# 컬럼마다 (익명명, 변환 방식, 파라미터) 를 정해 둔 표. 이 표가 곧 반출 스크립트 명세다.
#   spec : (x - target) / tol   — 스펙이 있는 값. 관리도·Cpk 가 그대로 나온다
#   z    : (x - 평균) / 표준편차 — 스펙을 모를 때. 상관·회귀가 그대로 나온다
#   rank : 백분위                — 순서만 남긴다. 회귀에는 못 쓴다
RULE = {
    '건조_ZONE2_TEMP':   ('TEMP_D2',  'spec', (120.0, 5.0)),
    '프레스_1호기_압력':  ('PRES_B1',  'z',    None),
    '코팅_로딩_mg_cm2':  ('LOAD_C1',  'z',    None),
    '화성_3단계_CV_전압': ('VOLT_P3',  'z',    None),
    'NMP_투입비':        ('RATIO_M2', 'rank', None),
}
for src, (dst, how, p) in RULE.items():
    print('%-18s -> %-9s %s' % (src, dst, how))"""),

    prep("""# 표대로 바꿔 주는 함수. 여기 코드는 안 고친다 — 위의 RULE 만 고친다.
def export(df, rule):
    out = pd.DataFrame(index=df.index)
    for src, (dst, how, p) in rule.items():
        x = df[src].astype(float)
        if   how == 'spec': out[dst] = ((x - p[0]) / p[1]).round(3)
        elif how == 'z':    out[dst] = ((x - x.mean()) / x.std()).round(3)
        elif how == 'rank': out[dst] = x.rank(pct=True).round(3)
    out['LOT'] = pd.factorize(df['로트번호'])[0]        # 순번을 지운다
    out['MC']  = pd.factorize(df['설비호기'])[0]        # 호기 이름을 지운다
    out['T']   = ((df['시각'] - df['시각'].min())
                  .dt.total_seconds() / 3600).round(2)  # t0 기준 시간
    return out"""),

    prep("""# 반출본을 만들어 본다
out = export(df, RULE)
print(out.head(3).to_string(index=False))"""),

    md("이제 `-0.32` 만 보고는 건조 온도가 **80도대인지 120도대인지 알 수 없다**.\n"
       "`LOT` 은 0 부터 다시 매겨 생산량이 안 보이고, `T` 는 첫 행을 0 으로 잡은 상대 시간이다."),

    md("### 나가도 되는 모양인지 자동으로 본다"),

    prep("""# 사람 눈으로 매번 보지 않는다. 검사기를 하나 만들어 두고 그것만 통과시킨다.
def check(out, src, rule):
    bad = []
    ko = [c for c in out.columns if any('가' <= ch <= '힣' for ch in c)]
    if ko:
        bad.append('한글 컬럼명이 남았다: %s' % ko)
    same = [c for c in out.columns if c in src.columns]
    if same:
        bad.append('원본 컬럼명이 그대로다: %s' % same)
    for c in out.columns:
        for s in src.select_dtypes('number').columns:
            if out[c].round(3).equals(src[s].round(3)):
                bad.append('%s 가 원본 %s 와 같은 값이다' % (c, s))
    print('\\n'.join(bad) if bad else '내보내도 되는 모양이다')

check(out, df, RULE)"""),

    md("### 분석 결과가 정말 그대로 나오는지"),

    code("""# 원본에서 잰 상관과 반출본에서 잰 상관을 견준다
pair = [('건조_ZONE2_TEMP', 'TEMP_D2'), ('프레스_1호기_압력', 'PRES_B1'),
        ('코팅_로딩_mg_cm2', 'LOAD_C1')]
a = df[[s for s, _ in pair]].corr().round(3).values
b = out[[d for _, d in pair]].corr().round(3).values
print('원본 상관\\n', a)
print('반출본 상관\\n', b)
print('같은가:', (a == b).all())"""),

    md("**같다.** 상관·회귀·관리도 판정·이상탐지·PCA 는 값을 선형으로 옮겨도 결과가 안 바뀐다.\n"
       "그래서 절대값을 안 넘기고도 분석 코드는 그대로 만들 수 있다."),

    Ex(4, "`RULE` 에서 `NMP_투입비` 의 방식을 `'rank'` 에서 `'z'` 로 바꾸고 다시 만들어 본다.\n"
          "> 방식 이름 한 글자만 바꾸면 된다. 함수는 안 고친다.\n"
          "> 분위 변환은 순서만 남기고 선형성이 깨져서 회귀에 못 쓴다는 것을 눈으로 본다.",
       setup="# RULE 의 값 부분만 바꾸는 문제다",
       blank="RULE['NMP_투입비'] = ('RATIO_M2', '___', None)",
       answer="RULE['NMP_투입비'] = ('RATIO_M2', 'z', None)",
       check="""out2 = export(df, RULE)
print('rank 일 때 상관', round(out['RATIO_M2'].corr(out['TEMP_D2']), 3))
print('z 일 때 상관   ', round(out2['RATIO_M2'].corr(out2['TEMP_D2']), 3))
print('원본 상관      ', round(df['NMP_투입비'].corr(df['건조_ZONE2_TEMP']), 3))"""),

    md("### 매핑 표는 사내에만 둔다"),

    code("""# 어느 익명명이 무엇이었는지는 로컬 파일로만 남긴다. 이 파일은 절대 밖으로 나가지 않는다.
mapping = pd.DataFrame([(s, d, h, str(p)) for s, (d, h, p) in RULE.items()],
                       columns=['원본명', '익명명', '방식', '파라미터'])
mapping.to_csv('mapping_local.csv', index=False)
print(mapping.to_string(index=False))"""),

    md("이 표가 **반출 스크립트 명세**다. 한 번 정해 두면 컬럼이 늘어도 매번 판단할 일이 없다."),

    Task(4, "`df` 를 **자기 업무 표**로 바꾸고, 컬럼마다 `RULE` 을 채운다.\n"
            "> ① 익명명은 「물리량_순번」 으로 짓는다 — 공정 이름·설비 이름은 넣지 않는다.\n"
            "> ② 스펙이 있으면 `spec`, 없으면 `z`, 순서만 보면 되면 `rank`.\n"
            "> ③ `check()` 가 「내보내도 되는 모양이다」를 찍을 때까지 고친다.",
         blank="""MY_RULE = {
    '___': ('___', '___', ___),
    '___': ('___', '___', ___),
}
my_out = export(df, MY_RULE)
check(my_out, df, MY_RULE)""",
         answer="""MY_RULE = {
    '건조_ZONE2_TEMP':  ('TEMP_D2', 'spec', (120.0, 5.0)),
    '코팅_로딩_mg_cm2': ('LOAD_C1', 'z',    None),
}
my_out = export(df, MY_RULE)
check(my_out, df, MY_RULE)""",
         check="print(my_out.head(3).to_string(index=False))"),

    md("### 사내에 붙일 때 챙길 것\n\n"
       "| 챙길 것 | 왜 |\n|---|---|\n"
       "| 데이터는 도구 안에 둔다 | 표를 프롬프트에 통째로 넣으면 그대로 반출이다 |\n"
       "| 도구 하나는 일 하나만 | 여러 일을 하면 모델이 오용한다 |\n"
       "| 에러는 고칠 방법까지 | 모델이 그 문구를 읽고 다시 고른다 |\n"
       "| 되돌릴 수 없는 일은 확인 | 삭제 · 발주 · 발송은 사람에게 묻는다 |\n"
       "| 부른 도구와 인자를 로그로 | 안 보이면 못 고친다 |"),
]

MODES = {
    ("ex", 1): "together", ("ex", 2): "together", ("ex", 3): "solo",
    ("ex", 4): "together",
    ("task", 1): "solo", ("task", 2): "solo", ("task", 3): "team",
    ("task", 4): "solo",
}

SPEC = ("에이전트의 구조", "설비 일지를 대신 찾아 주는 비서를 만든다", CELLS, MODES)
