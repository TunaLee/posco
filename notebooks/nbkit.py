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


def prep(src):
    """세 벌 모두에 들어가는 준비 셀 — 문제들이 쓰는 이름을 만든다"""
    c = code(src)
    c["metadata"] = {"always": True}
    return c

MODES = {
    "together": "같이 풀기",
    "solo":     "스스로",
    "team":     "조별로",
}


GROUPS = [
    ("together", "같이 풀기",  "수업 중에 같이 푼다."),
    ("solo",     "스스로 풀기", "각자 푼다. 막히면 손을 든다."),
    ("team",     "조별 과제",   "2~3명이 한 조로 상의하며 푼다."),
]

GROUPS_LAB = [                      # day3 부터 — 실습 시간에 강사와 같이 본다
    ("together", "같이 풀기",  "수업 중에 같이 푼다."),
    ("solo",     "스스로 풀기", "각자 푼다. 막히면 손을 든다."),
    ("team",     "조별로 풀기", "2~3명이 한 조로 상의하며 푼다."),
]


def q(no, text):
    return md(f"> **빈칸 문제 {no}.** {text}")


def t(no, text):
    return md(f"> **실습문제 {no}.** {text}")

class Task:
    """실습문제 — blank 를 주면 그 뼈대를 채우게 하고, 없으면 빈 자리를 준다"""
    kind = "task"

    def __init__(self, no, prompt, answer, check, setup="", blank=None):
        self.no, self.prompt, self.answer, self.check = no, prompt, answer, check
        self.setup, self.blank = setup, blank
        self.mode = "solo"

    def cells(self, solution):
        if solution:
            body = self.answer
        else:
            body = self.blank if self.blank else "# 여기에 작성한다\n"
        src = "\n".join(x for x in (self.setup, body, "", self.check) if x)
        return [t(getattr(self, "display_no", self.no), self.prompt), code(src)]


class Ex:
    """빈칸 문제 — blank/answer 두 벌로 갈린다"""
    kind = "ex"

    def __init__(self, no, prompt, blank, answer, check, setup=""):
        self.no, self.prompt, self.blank, self.answer = no, prompt, blank, answer
        self.check, self.setup = check, setup
        self.mode = "solo"

    def cells(self, solution):
        no_blank = getattr(self, "no_blank", False)
        if solution:
            body = self.answer
        else:
            body = "# 여기에 작성한다\n" if no_blank else self.blank
        src = "\n".join(x for x in (self.setup, body, "", self.check) if x is not None)
        head = t if no_blank else q
        return [head(getattr(self, "display_no", self.no), self.prompt), code(src)]


VARIANTS = {
    # 파일 이름       (설명,   담을 문제 모드,               코드를 채워 둘지)
    "live":     ("강의", ("together",),                True),
    "lab":      ("실습", ("solo", "team"),             False),
    "solution": ("정답", ("together", "solo", "team"), True),
}

INTRO = {
    "live": """수업을 따라가며 진행한다.

모든 셀에 **코드가 채워져 있다.** 위에서부터 실행해 결과를 눈으로 확인한다.
강사가 설명하는 동안 값을 바꿔 가며 돌려 본다.""",
    "lab": """강의가 끝난 뒤에 푼다. **강의 노트북에 없던 문제**들이다.

`스스로 풀기` 는 각자, `조별 과제` 는 2~3명이 한 조로 상의하며 푼다.
막히면 강의 노트북(`live`)에서 같은 함수를 쓴 셀을 찾아 대조한다.""",
    "solution": """`live` 와 `lab` 의 모든 문제에 대한 정답본이다.
수강생은 먼저 스스로 풀어 본 뒤에 연다.

두 벌을 합쳐 담으므로 **문제 번호가 `lab` 과 다르다.** 번호 대신
**지문으로 찾는다.**""",
}

INTRO_LAB = dict(INTRO, lab="""실습 시간에 푼다. **강의 노트북에 없던 문제**들이다.

`스스로 풀기` 는 각자, `조별로 풀기` 는 2~3명이 한 조로 상의하며 푼다.
막히면 강의 노트북(`live`)에서 같은 함수를 쓴 셀을 찾아 대조한다.""")


def build(day, title, subtitle, spec, variant, modes=None, renumber=False,
          no_blank=False, lab=False):
    desc, keep, solution = VARIANTS[variant]
    groups = GROUPS_LAB if lab else GROUPS
    intro  = (INTRO_LAB if lab else INTRO)[variant]
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

{intro}

문제는 실행하면 `assert` 로 자가 채점된다. 맞으면 `통과` 가 찍히고,
틀리면 기대값과 실제값이 같이 나온다.
""")]

    pending, section_open = [], None
    seq = {"ex": 0, "task": 0}          # 벌 안에서 1번부터 다시 센다

    def flush():
        for key, label, how in groups:
            if key not in keep:
                continue
            group = [x for x in pending if x.mode == key]
            if not group:
                continue
            if len(keep) > 1:
                cells.append(md(f"### {label}\n\n{how}"))
            for x in group:
                x.no_blank = no_blank and key == "together"
                if renumber:
                    # 머리글이 같은 것끼리 한 줄기로 센다
                    k = "task" if (x.no_blank or x.kind == "task") else "ex"
                    seq[k] += 1
                    x.display_no = seq[k]
                else:
                    x.display_no = x.no
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
            # 준비 셀은 세 벌 모두에, 데모·설명 셀은 lecture 에만 담는다
            if item.get("metadata", {}).get("always") or variant == "live":
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


def emit(day, title, subtitle, spec, modes=None, renumber=False,
         no_blank=False, lab=False):
    for variant in VARIANTS:
        p, n = build(day, title, subtitle, spec, variant, modes, renumber,
                     no_blank, lab)
        print(f"  {os.path.basename(p):<26} 코드 셀 {n:>3}개")
