#!/usr/bin/env python3
"""제출된 시험 노트북을 다시 실행해 채점한다.

  python3 notebooks/grade_exam.py 제출폴더/            → 점수.csv
  python3 notebooks/grade_exam.py 제출폴더/ -o 결과.csv

디스코드에서 받은 .ipynb 를 한 폴더에 모아 두고 돌린다.
출력에 든 값을 믿지 않고 **답 셀을 직접 실행해** 검사 셀로 판정한다.
"""
import json, io, os, sys, csv, re, traceback, warnings, argparse, contextlib
warnings.filterwarnings("ignore")


def cells_by_tag(nb):
    out = {}
    for c in nb.get("cells", []):
        t = c.get("metadata", {}).get("exam")
        if t and c["cell_type"] == "code":
            out.setdefault(t, []).append("".join(c["source"]))
    return out


def student_name(nb):
    for c in nb.get("cells", []):
        if c.get("metadata", {}).get("exam") == "grade":
            m = re.search(r'이름\s*=\s*["\']([^"\']*)["\']', "".join(c["source"]))
            if m and m.group(1).strip():
                return m.group(1).strip()
    return ""


def grade(path):
    nb = json.load(io.open(path, encoding="utf-8"))
    tags = cells_by_tag(nb)
    name = student_name(nb)
    g = {"__name__": "__main__"}
    # 준비 셀
    for src in tags.get("setup", []):
        try:
            exec(compile(src, "<setup>", "exec"), g)
        except Exception:
            pass
    nos, res = [], {}
    for t in tags:
        m = re.fullmatch(r"q(\d+)", t)
        if m:
            nos.append(int(m.group(1)))
    for no in sorted(nos):
        ok = False
        err = ""
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                for src in tags["q%d" % no]:
                    exec(compile(src, "<q%d>" % no, "exec"), g)
                for src in tags.get("check%d" % no, []):
                    exec(compile(src, "<c%d>" % no, "exec"), g)
            ok = True
        except Exception as e:
            err = "%s: %s" % (type(e).__name__, str(e)[:70])
        res[no] = (ok, err)
    return name, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("-o", "--out", default="점수.csv")
    ap.add_argument("--per", type=int, default=5)
    a = ap.parse_args()

    files = sorted(f for f in os.listdir(a.folder) if f.endswith(".ipynb"))
    if not files:
        print("제출된 .ipynb 가 없다:", a.folder)
        return 1
    rows, nums = [], set()
    for f in files:
        p = os.path.join(a.folder, f)
        try:
            name, res = grade(p)
        except Exception as e:
            print("  %-40s 열지 못했다 — %s" % (f, str(e)[:50]))
            continue
        nums |= set(res)
        got = sum(1 for ok, _ in res.values() if ok)
        rows.append((name or os.path.splitext(f)[0], f, res, got))
        wrong = [str(n) for n in sorted(res) if not res[n][0]]
        print("  %-24s %-34s %2d/%2d  %3d점   틀린 문항 %s"
              % ((name or "이름없음")[:24], f[:34], got, len(res), got * a.per,
                 ",".join(wrong) if wrong else "없음"))

    nums = sorted(nums)
    with io.open(a.out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["이름", "파일", "맞힌 문항", "점수"] + ["%d번" % n for n in nums])
        for name, f, res, got in rows:
            w.writerow([name, f, got, got * a.per]
                       + ["O" if res.get(n, (False,))[0] else "X" for n in nums])
    print("\n제출 %d명 · 평균 %.1f점 → %s"
          % (len(rows), sum(r[3] for r in rows) * a.per / max(len(rows), 1), a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
