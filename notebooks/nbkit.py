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

GROUPS = [
    ("solo", "스스로 풀기", "각자 푼다. 막히면 위 실습 셀로 돌아가 확인한다."),
    ("team", "조별 과제",   "2~3명이 한 조로 상의하며 푼다."),
]


def q(no, text):
    return md(f"> **빈칸 문제 {no}.** {text}")


def t(no, text):
    return md(f"> **실습문제 {no}.** {text}")

class Task:
    """실습문제 — 빈 자리에 직접 작성한다"""
    kind = "task"

    def __init__(self, no, prompt, answer, check, setup=""):
        self.no, self.prompt, self.answer, self.check, self.setup = no, prompt, answer, check, setup
        self.mode = "solo"

    def cells(self, solution):
        body = self.answer if solution else "# 여기에 작성한다\n"
        src = "\n".join(x for x in (self.setup, body, "", self.check) if x)
        return [t(self.no, self.prompt), code(src)]


class Ex:
    """빈칸 문제 — blank/answer 두 벌로 갈린다"""
    kind = "ex"

    def __init__(self, no, prompt, blank, answer, check, setup=""):
        self.no, self.prompt, self.blank, self.answer = no, prompt, blank, answer
        self.check, self.setup = check, setup
        self.mode = "solo"

    def cells(self, solution):
        body = self.answer if solution else self.blank
        src = "\n".join(x for x in (self.setup, body, "", self.check) if x is not None)
        return [q(self.no, self.prompt), code(src)]


VARIANTS = {
    # 파일 이름         (설명,    담을 문제 모드,     정답 여부)
    "practice": ("실습",   ("solo", "team"),  False),
    "solution": ("정답",   ("solo", "team"),  True),
}

INTRO = {
    "practice": """각 절은 **실습 → 스스로 풀기 → 조별 과제** 순으로 이어진다.

**실습** 셀은 그대로 실행해 결과를 눈으로 확인한다.
`스스로 풀기` 는 각자, `조별 과제` 는 2~3명이 한 조로 상의하며 푼다.""",
    "solution": """`practice` 의 정답본이다. 먼저 스스로 풀어 본 뒤에 연다.""",
}


def build(day, title, subtitle, spec, variant, modes=None):
    desc, keep, solution = VARIANTS[variant]
    url = (f"https://colab.research.google.com/github/{REPO}"
           f"/blob/main/notebooks/day{day}_{variant}.ipynb")

    cells = [md(f"""
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})

# Day {day} · {desc} — {title}

{subtitle}

---

### 시작하기 전에

1. **파일 → 드라이브에 사본 저장** 을 먼저 누른다. 안 하면 고친 내용이 남지 않는다.
2. 셀을 고르고 **Shift + Enter** 로 실행한다.

{INTRO[variant]}

문제는 실행하면 `assert` 로 자가 채점된다. 맞으면 `통과` 가 찍히고,
틀리면 기대값과 실제값이 같이 나온다.
""")]

    pending, section_open = [], None

    def flush():
        for key, label, how in GROUPS:
            if key not in keep:
                continue
            group = [x for x in pending if x.mode == key]
            if not group:
                continue
            if len(keep) > 1:
                cells.append(md(f"### {label}\n\n{how}"))
            for x in group:
                cells.extend(x.cells(solution))
        pending.clear()

    def is_section(cell):
        return cell["cell_type"] == "markdown" and "".join(cell["source"]).startswith("## ")

    for item in spec:
        if isinstance(item, (Ex, Task)):
            item.mode = (modes or {}).get((item.kind, item.no), "solo")
            pending.append(item)
        elif is_section(item):
            flush()
            section_open = item
            cells.append(item)
        else:
            # 데모·설명 셀은 실습본에만 담는다
            if variant == "practice":
                cells.append(item)
    flush()

    # 문제가 하나도 없는 절 머리글은 지운다
    pruned, i = [], 0
    while i < len(cells):
        c = cells[i]
        if (c["cell_type"] == "markdown" and "".join(c["source"]).startswith("## ")
                and (i + 1 == len(cells) or
                     ("".join(cells[i + 1]["source"]).startswith("## ")))):
            i += 1
            continue
        pruned.append(c)
        i += 1

    nb = {"cells": pruned,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python", "version": "3.11"},
                       "colab": {"provenance": [], "toc_visible": True}},
          "nbformat": 4, "nbformat_minor": 0}
    path = os.path.join(HERE, f"day{day}_{variant}.ipynb")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    return path, sum(1 for c in pruned if c["cell_type"] == "code")


def emit(day, title, subtitle, spec, modes=None):
    for variant in VARIANTS:
        p, n = build(day, title, subtitle, spec, variant, modes)
        print(f"  {os.path.basename(p):<26} 코드 셀 {n:>3}개")
