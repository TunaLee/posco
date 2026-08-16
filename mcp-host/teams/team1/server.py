# 1조 — 설비 점검
import pandas as pd
from fastmcp import FastMCP

BASE = 'https://tunalee.github.io/posco/data/'
df = pd.read_csv(BASE + 'cell_process.csv')
mcp = FastMCP('설비 점검')

OPEN = ['로트번호', '시각', '설비호기', '교대조', '판정']    # 내보내도 되는 칸
LIMIT = 20

@mcp.tool()
def defect_rate(machine: str, shift: str = '') -> str:
    '''설비호기의 불량률을 돌려준다. 교대조를 주면 그 조만 센다.

    machine: 설비호기. 1호기 ~ 4호기
    shift: 주간 또는 야간. 비우면 전체
    '''
    d = df[df['설비호기'] == machine]
    if shift:
        d = d[d['교대조'] == shift]
    if not len(d):
        return '해당 데이터가 없다. 설비: ' + ', '.join(sorted(df['설비호기'].unique()))
    bad = int((d['판정'] == '불량').sum())
    return '%s %s 측정 %d건 중 불량 %d건 · %.1f%%' % (
        machine, shift or '전체', len(d), bad, 100.0 * bad / len(d))

@mcp.tool()
def recent_lots(machine: str, n: int = 5) -> str:
    '''설비의 최근 로트 기록을 돌려준다. 공정 조건값은 내보내지 않는다.

    machine: 설비호기. 1호기 ~ 4호기
    n: 몇 건. 최대 20
    '''
    d = df[df['설비호기'] == machine].tail(min(n, LIMIT))
    if not len(d):
        return '해당 설비가 없다'
    return d[OPEN].to_string(index=False)

if __name__ == '__main__':
    mcp.run()
