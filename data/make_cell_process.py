#!/usr/bin/env python3
"""강의용 합성 이차전지 셀 공정 시계열 생성기.  python3 data/make_cell_process.py

실제 데이터가 아니다. 난수로 만든 가상의 셀 제조 라인 기록이다.
회사·설비·제품을 특정하지 않는다. 값은 문헌에 흔히 보이는 범위 안에서 임의로 잡았다.

만드는 파일
  docs/data/cell_process.csv    공정 기록 2,400행 — 반출본 만들기 실습에 쓴다

이 데이터는 「그대로 내보내면 안 되는 표」의 본보기다.
  컬럼명    화성_3단계_CV_전압 · NMP_투입비 처럼 이름만으로 레시피가 드러난다
  값        건조 온도 118.4, 코팅 로딩 21.3 처럼 절대값이 곧 설계값이다
  로트 ID   LOT-2026-1200 부터 순번이라 증가율로 생산량이 역산된다
  타임스탬프 3분 간격이라 tact time 이 그대로 보인다

전처리로 잡을 것도 같이 심어 둔다
  센서 단선   건조_ZONE2_TEMP 에 연속 결측 40행
  값 고착     프레스_1호기_압력 이 같은 값으로 60행 붙어 있다
  단위 혼입   건조_ZONE1_TEMP 일부가 화씨로 들어온다
  레벨 시프트  로트가 바뀌는 자리에서 코팅 로딩이 계단으로 뛴다
  시각 사고   타임스탬프 역행 6건 · 중복 9건
"""
import csv
import datetime
import os
import random

SEED = 20260811
N = 2400
STEP = datetime.timedelta(minutes=3)
T0 = datetime.datetime(2026, 8, 3, 6, 0)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "data")

COLS = ["로트번호", "시각", "설비호기", "교대조",
        "건조_ZONE1_TEMP", "건조_ZONE2_TEMP", "프레스_1호기_압력",
        "코팅_로딩_mg_cm2", "전극_밀도", "화성_3단계_CV_전압",
        "NMP_투입비", "에이징_시간_h", "판정"]

MACHINES = ["1호기", "2호기", "3호기", "4호기"]


def build():
    rnd = random.Random(SEED)
    rows = []
    lot_base = 1200
    # 로트마다 조금씩 다른 기준점 — 로트 경계에서 값이 계단으로 뛴다
    lot_shift = {}
    for i in range(N):
        lot_no = lot_base + i // 40
        if lot_no not in lot_shift:
            lot_shift[lot_no] = rnd.choice([-0.35, -0.15, 0.0, 0.0, 0.2, 0.45])
        shift = lot_shift[lot_no]
        t = T0 + STEP * i
        mc = MACHINES[i % 4]
        shiftname = "주간" if 6 <= t.hour < 18 else "야간"

        # 완만한 드리프트 — 시간이 갈수록 건조로가 조금씩 식는다
        drift = -1.2 * (i / N)
        z1 = round(rnd.gauss(132.0 + drift, 1.8), 1)
        z2 = round(rnd.gauss(118.5 + drift, 2.1), 1)
        # 간헐 스파이크
        if rnd.random() < 0.012:
            z2 = round(z2 + rnd.choice([-9.0, 9.5, 11.0]), 1)

        pres = round(rnd.gauss(1450, 58), 0)
        load = round(rnd.gauss(21.3 + shift, 0.55), 2)
        dens = round(rnd.gauss(3.48, 0.04) + shift * 0.02, 3)
        volt = round(rnd.gauss(4.190, 0.009), 3)
        ratio = round(rnd.gauss(0.420, 0.018), 3)
        aging = round(rnd.choice([24, 24, 36, 48]) + rnd.gauss(0, 0.4), 1)

        # 판정 — 로딩과 밀도가 스펙을 벗어나면 불량 쪽으로 기운다
        risk = abs(load - 21.3) / 0.55 + abs(dens - 3.48) / 0.04 * 0.6
        bad = risk > 2.4 or rnd.random() < 0.03
        rows.append([f"LOT-2026-{lot_no:04d}", t, mc, shiftname,
                     z1, z2, pres, load, dens, volt, ratio, aging,
                     "불량" if bad else "양품"])

    # ── 일부러 심는 것 ──────────────────────────────────────────────
    # 센서 단선 — 연속 결측
    for i in range(820, 860):
        rows[i][5] = ""
    # 값 고착 — 같은 값이 붙어 있다
    stuck = rows[1500][6]
    for i in range(1500, 1560):
        rows[i][6] = stuck
    # 단위 혼입 — ZONE1 일부가 화씨로 들어온다
    for i in range(300, 348):
        rows[i][4] = round(rows[i][4] * 9 / 5 + 32, 1)
    # 타임스탬프 역행
    for i in (410, 411, 990, 991, 1802, 1803):
        rows[i][1] = rows[i][1] - STEP * 2
    # 타임스탬프 중복
    for i in (200, 201, 202, 700, 701, 1300, 1301, 2100, 2101):
        rows[i][1] = rows[i - 1][1]

    for r in rows:
        r[1] = r[1].strftime("%Y-%m-%d %H:%M:%S")
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = build()
    p = os.path.join(OUT, "cell_process.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        w.writerows(rows)
    bad = sum(1 for r in rows if r[-1] == "불량")
    print("%s  %d행 %d열  불량 %d건 (%.1f%%)"
          % (p, len(rows), len(COLS), bad, bad / len(rows) * 100))


if __name__ == "__main__":
    main()
