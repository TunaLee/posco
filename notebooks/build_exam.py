#!/usr/bin/env python3
"""1주차 시험 노트북 생성기.  python3 notebooks/build_exam.py

  exam1.ipynb         수강생용 — 빈칸
  exam1_answer.ipynb  강사용   — 정답
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exam1_spec as S

HERE = os.path.dirname(os.path.abspath(__file__))


def _lines(t):
    p = t.strip("\n").split("\n")
    return [x + "\n" for x in p[:-1]] + [p[-1]]


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(t)}


def code(src, tag=None):
    c = {"cell_type": "code", "execution_count": None, "metadata": {},
         "outputs": [], "source": _lines(src)}
    if tag:
        c["metadata"] = {"exam": tag}
    return c


HEAD = """# {title}

**푸는 법**

1. 위에서부터 차례로 실행한다. 앞 문제의 결과를 뒤에서 쓰는 문제가 있다.
2. `___` 를 채운다. 그 줄만 고치고 나머지는 건드리지 않는다.
3. 문제마다 아래 **[검사]** 셀을 실행해 통과를 확인한다. 빨간 글씨가 나오면 아직 틀린 것이다.
4. 다 풀면 맨 아래 **채점** 셀을 실행한다.

**제출하는 법**

1. 맨 아래 채점 셀까지 실행한 뒤 저장한다 &mdash; `Ctrl+S` (Mac 은 `Cmd+S`)
2. 메뉴에서 `파일` → `.ipynb 다운로드`
3. 내려받은 파일을 **디스코드 제출 채널에 올린다.** 파일 이름은 그대로 둔다.

배점은 문항당 {per}점, 모두 {total}점이다.

---"""

FOOT_STUDENT = """---

## 채점

아래 셀을 실행하면 몇 개를 맞혔는지 나온다. **실행한 뒤 저장하고 내려받아 제출한다.**"""

GRADE_CELL = """이름 = ""   # 여기에 이름을 적는다

# ── 아래는 고치지 않는다 ──────────────────────────────────────────────
import io, json, re
_nb = None
for _p in ('exam1.ipynb', '/content/exam1.ipynb'):
    try:
        _nb = json.load(io.open(_p, encoding='utf-8')); break
    except Exception:
        pass
print("이름:", 이름 if 이름 else "(비어 있다 — 이름을 적고 다시 실행한다)")
print()
_ok = []
for _no, _fn in sorted(_CHECKS.items()):
    try:
        _fn(); _ok.append(_no)
    except Exception as _e:
        print("  %2d번  아직 안 됨  %s" % (_no, str(_e)[:60]))
print()
print("맞힌 문항 %d / %d" % (len(_ok), _TOTAL_N))
print("점수      %d / %d" % (len(_ok) * _PER, _TOTAL_N * _PER))
print()
print("제출 파일 이름:  1주차시험_%s.ipynb" % (이름 or "이름"))"""


def build(answer: bool):
    cells = [md(HEAD.format(title=S.TITLE, per=S.ITEMS[0][1], total=S.TOTAL))]
    # 검사 함수를 모아 둘 자리
    cells.append(code("_CHECKS = {}\n_PER = %d\n_TOTAL_N = %d" % (S.ITEMS[0][1], len(S.ITEMS)),
                      tag="setup"))
    area = None
    for no, pt, ar, prompt, blank, ans, chk in S.ITEMS:
        if ar != area:
            area = ar
            cells.append(md("## %s" % ar))
        cells.append(md("**문제 %d.** (%d점) %s" % (no, pt, prompt)))
        cells.append(code(ans if answer else blank, tag="q%d" % no))
        body = "\n".join("    " + l for l in chk.split("\n"))
        cells.append(code("# [검사] 이 셀은 고치지 않는다\n"
                          "def _c%d():\n%s\n_CHECKS[%d] = _c%d\n_c%d()\nprint('%d번 통과')"
                          % (no, body, no, no, no, no), tag="check%d" % no))
    cells.append(md(FOOT_STUDENT))
    cells.append(code(GRADE_CELL, tag="grade"))
    return {"cells": cells,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                        "name": "python3"},
                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5}


if __name__ == "__main__":
    for ans, name in ((False, "exam1.ipynb"), (True, "exam1_answer.ipynb")):
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(build(ans), f, ensure_ascii=False, indent=1)
        n = sum(1 for c in build(ans)["cells"] if c["cell_type"] == "code")
        print("  %-22s 문항 %d개 · 코드 셀 %d개 · 총 %d점"
              % (name, len(S.ITEMS), n, S.TOTAL))
