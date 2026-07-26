"""노트북 생성 헬퍼 — 셀 빌더와 문제 클래스."""
import json, os, sys

REPO = "TunaLee/posco"
HERE = os.path.dirname(os.path.abspath(__file__))

# ── 셀 헬퍼 ────────────────────────────────────────────────────────────
def _lines(text):
    """nbformat 의 source 리스트 — 마지막 줄을 뺀 각 줄이 개행을 품어야 한다."""
    parts = text.strip("\n").split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}

def code(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": _lines(src)}

def h(level, text):
    return md("#" * level + " " + text)

def lab(text):
    """따라 해 보는 실습 안내"""
    return md(f"**실습.** {text}")

def q(no, text):
    """빈칸 문제 안내"""
    return md(f"> **문제 {no}.** {text}")

class Ex:
    """빈칸 문제 — blank/answer 두 벌로 갈린다"""
    def __init__(self, no, prompt, blank, answer, check, setup=""):
        self.no, self.prompt, self.blank, self.answer = no, prompt, blank, answer
        self.check, self.setup = check, setup

    def cells(self, solution):
        body = self.answer if solution else self.blank
        src = "\n".join(x for x in (self.setup, body, "", self.check) if x is not None)
        return [q(self.no, self.prompt), code(src)]


def build(day, title, subtitle, spec, solution):
    nb_cells = []
    suffix = "_solution" if solution else ""
    url = f"https://colab.research.google.com/github/{REPO}/blob/main/notebooks/day{day}{suffix}.ipynb"
    nb_cells.append(md(f"""
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})

# Day {day} 실습 — {title}

{subtitle}

---

### 시작하기 전에

1. 위 메뉴에서 **파일 → 드라이브에 사본 저장** 을 먼저 누른다.
   이걸 안 하면 고친 내용이 저장되지 않는다.
2. 셀을 고르고 **Shift + Enter** 로 실행한다. 왼쪽 `[1]` 은 실행 순서다.
3. **실습** 셀은 그대로 실행해 결과를 눈으로 확인한다.
4. **문제** 셀의 `___` 를 채운 뒤 실행한다. 맞으면 `통과` 가 찍힌다.
"""))
    for item in spec:
        if isinstance(item, Ex):
            nb_cells += item.cells(solution)
        else:
            nb_cells.append(item)

    nb = {"cells": nb_cells,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python", "version": "3.11"},
                       "colab": {"provenance": [], "toc_visible": True}},
          "nbformat": 4, "nbformat_minor": 0}
    path = os.path.join(HERE, f"day{day}{suffix}.ipynb")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    return path, sum(1 for c in nb_cells if c["cell_type"] == "code")


def emit(day, title, subtitle, spec):
    n_ex = sum(1 for x in spec if isinstance(x, Ex))
    for sol in (False, True):
        p, n = build(day, title, subtitle, spec, sol)
        print(f"  {os.path.basename(p):<26} 코드 셀 {n:>3}개  문제 {n_ex}개")


