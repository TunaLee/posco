# 2조 — 규정 문답
import re
import urllib.request

import numpy as np
from fastmcp import FastMCP
from sklearn.feature_extraction.text import TfidfVectorizer

BASE = 'https://tunalee.github.io/posco/data/docs/'
FILES = {'근로기준법': 'labor_standards.txt', '산업안전보건법': 'occupational_safety.txt'}

CHUNKS = []
for name, fn in FILES.items():
    raw = urllib.request.urlopen(BASE + fn, timeout=60).read().decode('utf-8')
    text = '\n'.join(l for l in raw.split('\n') if not l.startswith('#'))
    for p in re.split(r'\n(?=제\d+조)', text):
        p = p.strip()
        if len(p) >= 40:
            CHUNKS.append({'source': name, 'title': p.split('\n')[0][:40], 'text': p})

# 글자 단위로 쪼개 견준다. 「멈출」과 「중지」처럼 낱말이 달라도 걸리게 하는 쪽이다.
TEXTS = [c['title'] * 3 + ' ' + c['text'] for c in CHUNKS]      # 제목을 세 번 세어 무겁게 친다
VEC = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), max_features=50000)
M = VEC.fit_transform(TEXTS)

mcp = FastMCP('규정 문답')


@mcp.tool()
def find_rule(question: str) -> str:
    '''사내 규정과 법령에서 관련 조문 셋을 찾아 돌려준다.
    한 번 부르면 충분하다. 같은 질문으로 다시 부르지 않는다.

    question: 찾고 싶은 내용. 보기 위험할 때 작업을 멈추는 근거
    '''
    sim = (M @ VEC.transform([question]).T).toarray().ravel()
    hits = np.argsort(-sim)[:3]
    if sim[hits[0]] < 0.02:
        return '관련 조문을 못 찾았다'
    return '\n\n'.join('[%s %s]\n%s' % (CHUNKS[i]['source'], CHUNKS[i]['title'],
                                        CHUNKS[i]['text'][:300]) for i in hits)


if __name__ == '__main__':
    mcp.run()
