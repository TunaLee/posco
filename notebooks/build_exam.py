#!/usr/bin/env python3
"""시험 노트북 생성기.  python3 notebooks/build_exam.py [주차...]

  exam<N>.ipynb         수강생용 — 빈칸
  exam<N>_answer.ipynb  강사용   — 정답

주차를 안 주면 exam<N>_spec.py 가 있는 것을 모두 만든다.
"""
import importlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


BADGE = ("[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
         "(https://colab.research.google.com/github/TunaLee/posco/blob/main/notebooks/exam%d.ipynb)")

HEAD = """{badge}

# {title}

**푸는 법**

1. 위에서부터 차례로 실행한다. 앞 문제의 결과를 뒤에서 쓰는 문제가 있다.
2. `___` 를 채운다. 그 줄만 고치고 나머지는 건드리지 않는다.
3. 문제마다 아래 **[검사]** 셀을 실행해 통과를 확인한다. 빨간 글씨가 나오면 아직 틀린 것이다.
4. 다 풀면 맨 아래 **채점** 셀을 실행한다.

**제출하는 법**

1. 맨 아래 채점 셀까지 실행한 뒤 저장한다 &mdash; `Ctrl+S` (Mac 은 `Cmd+S`)
2. 메뉴에서 `파일` → `.ipynb 다운로드`
3. 내려받은 파일을 제출한다. 파일 이름은 그대로 둔다.

배점은 문항당 {per}점, 모두 {total}점이다.

---"""

FOOT_STUDENT = """---

## 채점

아래 셀을 실행하면 몇 개를 맞혔는지 나온다. **실행한 뒤 저장하고 내려받아 제출한다.**"""

GRADE_CELL = """이름 = ""   # 여기에 이름을 적는다

# ── 아래는 고치지 않는다 ──────────────────────────────────────────────
import io, json, re
_nb = None
for _p in ('exam{WK}.ipynb', '/content/exam{WK}.ipynb'):
    try:
        _nb = json.load(io.open(_p, encoding='utf-8')); break
    except Exception:
        pass
print("이름:", 이름 if 이름 else "(비어 있다 — 이름을 적고 다시 실행한다)")
print()
_ok = [_no for _no, _v in sorted(_CHECKS.items()) if _v]
for _no in range(1, _TOTAL_N + 1):
    if _no not in _CHECKS:
        print("  %2d번  검사 셀을 아직 안 돌렸다" % _no)
    elif not _CHECKS[_no]:
        print("  %2d번  아직 안 됨" % _no)
print()
print("맞힌 문항 %d / %d" % (len(_ok), _TOTAL_N))
print("점수      %d / %d" % (len(_ok) * _PER, _TOTAL_N * _PER))
print()
print("제출 파일 이름:  {WK}주차시험_%s.ipynb" % (이름 or "이름"))"""


def build(S, wk, answer: bool):
    cells = [md(HEAD.format(badge=BADGE % wk, title=S.TITLE,
                            per=S.ITEMS[0][1], total=S.TOTAL))]
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
        # 검사 결과를 그 자리에서 기록한다. 뒤 문제가 같은 변수명을 덮어써도
        # 채점이 흔들리지 않는다.
        cells.append(code("# [검사] 이 셀은 고치지 않는다\n"
                          "def _c%d():\n%s\n"
                          "try:\n"
                          "    _c%d(); _CHECKS[%d] = True; print('%d번 통과')\n"
                          "except AssertionError:\n"
                          "    _CHECKS[%d] = False; raise"
                          % (no, body, no, no, no, no), tag="check%d" % no))
    cells.append(md(FOOT_STUDENT))
    cells.append(code(GRADE_CELL.replace("{WK}", str(wk)), tag="grade"))
    return {"cells": cells,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                        "name": "python3"},
                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5}


if __name__ == "__main__":
    weeks = [int(a) for a in sys.argv[1:]] or \
            sorted(int(f[4]) for f in os.listdir(HERE)
                   if f.startswith("exam") and f.endswith("_spec.py"))
    for wk in weeks:
        S = importlib.import_module("exam%d_spec" % wk)
        for ans, name in ((False, "exam%d.ipynb" % wk), (True, "exam%d_answer.ipynb" % wk)):
            nb = build(S, wk, ans)
            with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
                json.dump(nb, f, ensure_ascii=False, indent=1)
            n = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
            print("  %-22s 문항 %d개 · 코드 셀 %d개 · 총 %d점"
                  % (name, len(S.ITEMS), n, S.TOTAL))
