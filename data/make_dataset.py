#!/usr/bin/env python3
"""강의용 합성 양극재 소성 공정 데이터 생성기.  python3 data/make_dataset.py

실제 데이터가 아니다. 난수로 만든 가상의 이차전지 양극재 소성 배치 기록이다.
회사·설비·제품을 특정하지 않는다.

만드는 파일
  docs/data/batch_quality.csv   배치 1400건 — 전처리·학습에 쓴다 (열 이름은 한글)
  docs/data/line_master.csv     설비 마스터 6행 — merge 예제에 쓴다

가르칠 것을 의도적으로 심어 둔다
  결측       particle_size 8% · moisture 4% (표기가 'N/A' '-' '' 로 흔들린다)
  타입 사고   impurity 가 '1,240' 처럼 쉼표를 달고 와서 object 로 읽힌다
  표기 흔들림 설비호기 가 'A' 'a' ' A ' 로 섞여 들어온다
  이상치     press 에 센서 오류값 999.0
  중복       같은 배치가 두 번 기록된 행 12건
  불균형     불량 약 16% — 정확도만 보면 안 되는 예
  숨은 원인   설비 연식이 오래될수록 용량이 낮다. line_master 와 merge 해야 드러난다
"""
import csv
import os
import random

SEED = 20260727
N = 1400
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "data")

LINES = ["A", "B", "C", "D", "E", "F"]
# 설비 연식이 오래될수록 용량이 조금 낮다.
# line_master 와 merge 해 보면 installed_year 로 설명된다.
LINE_EFFECT = {"A": -2.2, "B": -2.0, "C": -0.6, "D": -0.5, "E": 0.4, "F": 0.5}
SHIFTS = ["day", "night"]
NA_TOKENS = ["N/A", "-", ""]


def rounded(x, n=1):
    return round(x, n)


def make_rows(rng):
    rows = []
    for i in range(1, N + 1):
        line = rng.choice(LINES)
        shift = rng.choices(SHIFTS, weights=[0.55, 0.45])[0]

        # 공정 조건
        calc_temp = rng.gauss(850, 28)                      # 소성 온도 °C
        calc_time = rng.choice([90, 105, 120, 135, 150])    # 소성 시간 min
        particle = rng.gauss(12.0, 2.4)                     # 원료 입도 µm
        moisture = abs(rng.gauss(1.2, 0.35))                # 수분율 %
        impurity = abs(rng.gauss(820, 340))                 # 불순물 ppm
        press = rng.gauss(24.0, 2.2)                        # 성형 압력 MPa

        # 야간조는 온도 편차가 조금 크다 — groupby 로 드러난다
        if shift == "night":
            calc_temp += rng.gauss(0, 12)

        # 방전 용량 — 온도에 최적점(890°C)이 있다. 대부분의 배치가 그 아래라
        # 상관은 뚜렷하게 양수로 나오지만, 관계 자체는 곡선이다.
        # 선형 회귀도 어느 정도 맞히고 트리 계열이 더 잘 맞히는 구조가 된다.
        cap = (
            190.0
            - 0.0020 * (calc_temp - 890) ** 2
            + 0.045 * (calc_time - 120)
            - 0.0042 * impurity
            - 3.0 * moisture
            - 0.35 * particle
            + LINE_EFFECT[line]
            + rng.gauss(0, 2.2)
        )

        passed = 1 if (cap >= 168.0 and impurity <= 1500) else 0

        rows.append({
            "배치번호": "B%05d" % i,
            "설비호기": line,
            "교대조": shift,
            "소성온도": rounded(calc_temp),
            "소성시간": calc_time,
            "입도": rounded(particle, 2),
            "수분율": rounded(moisture, 2),
            "불순물": int(impurity),
            "성형압력": rounded(press, 1),
            "방전용량": rounded(cap, 1),
            "양품여부": passed,
        })
    return rows


def dirty(rows, rng):
    """깨끗한 행에 현장에서 실제로 겪는 문제들을 입힌다."""
    for r in rows:
        # 표기 흔들림 — 같은 설비인데 대소문자와 공백이 다르다
        if rng.random() < 0.30:
            r["설비호기"] = rng.choice([r["설비호기"].lower(), " " + r["설비호기"], r["설비호기"] + " "])

        # 결측 — 표기가 통일돼 있지 않다
        if rng.random() < 0.08:
            r["입도"] = rng.choice(NA_TOKENS)
        if rng.random() < 0.04:
            r["수분율"] = rng.choice(NA_TOKENS)

        # 천 단위 쉼표가 붙어 문자열로 읽힌다
        if r["불순물"] >= 1000:
            r["불순물"] = "{:,}".format(r["불순물"])

        # 센서 오류 — 눈에 띄는 이상치
        if rng.random() < 0.015:
            r["성형압력"] = 999.0

    # 같은 배치가 두 번 기록된다
    for r in rng.sample(rows, 12):
        rows.append(dict(r))
    rng.shuffle(rows)
    return rows


def line_master():
    return [
        {"설비호기": "A", "설치연도": 2015, "정격온도": 850, "담당팀": "1팀"},
        {"설비호기": "B", "설치연도": 2015, "정격온도": 850, "담당팀": "1팀"},
        {"설비호기": "C", "설치연도": 2018, "정격온도": 870, "담당팀": "2팀"},
        {"설비호기": "D", "설치연도": 2018, "정격온도": 870, "담당팀": "2팀"},
        {"설비호기": "E", "설치연도": 2021, "정격온도": 880, "담당팀": "3팀"},
        {"설비호기": "F", "설치연도": 2021, "정격온도": 880, "담당팀": "3팀"},
    ]


def write(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    rng = random.Random(SEED)
    os.makedirs(OUT, exist_ok=True)

    rows = dirty(make_rows(rng), rng)
    fields = ["배치번호", "설비호기", "교대조", "소성온도", "소성시간",
              "입도", "수분율", "불순물", "성형압력", "방전용량", "양품여부"]
    write(os.path.join(OUT, "batch_quality.csv"), rows, fields)

    master = line_master()
    write(os.path.join(OUT, "line_master.csv"), master,
          ["설비호기", "설치연도", "정격온도", "담당팀"])

    bad = sum(1 for r in rows if r["양품여부"] == 0)
    print("batch_quality.csv  %d행 · 불량 %d건 (%.1f%%)" % (len(rows), bad, 100 * bad / len(rows)))
    print("line_master.csv    %d행" % len(master))


if __name__ == "__main__":
    main()
