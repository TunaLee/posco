# 공정 배치 데이터

**실제 데이터가 아니다.** 강의용으로 난수에서 만든 가상의 소성 공정 기록이다.
회사·설비·제품을 특정하지 않는다. 생성기는 [`data/make_dataset.py`](../../data/make_dataset.py)에 있고
시드가 고정돼 있어 언제 돌려도 같은 파일이 나온다.

## 불러오기

```python
import pandas as pd

url = 'https://tunalee.github.io/posco/data/batch_quality.csv'
df = pd.read_csv(url)
```

## batch_quality.csv — 1412행 11열

| 열 | 뜻 | 단위 | 비고 |
|---|---|---|---|
| `batch_id` | 배치 번호 | | 중복 12건이 섞여 있다 |
| `line` | 설비 호기 | A~F | 표기가 `'A'` `'a'` `' A '`로 흔들린다 |
| `shift` | 교대조 | day / night | 야간조는 온도 편차가 크다 |
| `calc_temp` | 소성 온도 | °C | 용량과 가장 관계가 깊다 |
| `calc_time` | 소성 시간 | min | 90 · 105 · 120 · 135 · 150 |
| `particle_size` | 원료 입도 | µm | **결측 8%** |
| `moisture` | 수분율 | % | **결측 4%** |
| `impurity` | 불순물 | ppm | **`'1,240'` 쉼표 탓에 문자로 읽힌다** |
| `press` | 성형 압력 | MPa | **센서 오류 `999.0` 18건** |
| `capacity` | 방전 용량 | mAh/g | **회귀 정답** |
| `passed` | 양품 여부 | 0 / 1 | **분류 정답** · 불량 18.8% |

## line_master.csv — 6행

| 열 | 뜻 |
|---|---|
| `line` | 설비 호기 |
| `installed_year` | 설치 연도 |
| `rated_temp` | 정격 온도 |
| `team` | 담당 팀 |

`batch_quality`와 `line`으로 `merge`하면 **설비가 오래될수록 불량률이 높다**는 것이 드러난다.

| 설치 연도 | 불량률 | 평균 용량 |
|---|---|---|
| 2015 (A·B) | 21.4% | 172.0 |
| 2018 (C·D) | 18.9% | 173.1 |
| 2021 (E·F) | 16.0% | 174.6 |

## 심어 둔 것

읽자마자 손봐야 할 것들이 일부러 들어 있다.

| 문제 | 어디에 | 배우는 것 |
|---|---|---|
| 결측 표기가 `N/A` `-` `''`로 제각각 | `particle_size` `moisture` | `na_values` · `isnull` · `fillna` |
| 천 단위 쉼표 탓에 `object` 타입 | `impurity` | `dtype` 확인 · `to_numeric` · `thousands=','` |
| 대소문자·공백 흔들림 | `line` | `str.strip().str.upper()` |
| 센서 오류값 | `press` | 이상치 탐지 · 박스플롯 |
| 같은 배치가 두 번 | 12행 | `duplicated` · `drop_duplicates` |
| 정답 불균형 18.8% | `passed` | 정확도의 함정 · 정밀도/재현율 |
| 답과 무관한 열 | `press` (상관 −0.04) | 상관 히트맵 읽기 |

## capacity 와의 상관

```
calc_temp      +0.76      ← 가장 강하다
impurity       −0.25
particle_size  −0.16
moisture       −0.14
calc_time      +0.17
press          −0.04      ← 사실상 무관
```

온도는 **890 °C 부근이 최적**이고 대부분의 배치가 그 아래에 있다.
그래서 상관은 뚜렷한 양수로 나오지만 관계 자체는 곡선이다 —
선형 회귀도 어느 정도 맞히고, 트리 계열이 더 잘 맞힌다.
