# Relative Strength (§35)

> 원본: `micro Ideation/35_relative_strength.md.pdf` | Price Layer | **T0~T2 중심축**

## 핵심 질문

시장은 실제로 무엇을 사고 있는가? — "주가는 시장의 투표 결과이며, RS는 그 결과를 측정한다."

## 3계층 RS

Market RS(vs SPY/QQQ) → Sector RS(vs 섹터ETF, 예 NVDA vs SMH) → Peer RS(동종기업 내 위치, 예 NVDA/AMD/AVGO/MU/MRVL 비교) + Momentum Component(1/3/6/12M 변화율)

## Composite State

Dominant Leader(시장+섹터+Peer 모두 강함) > Leader(강함) > Emerging(개선 중) > Average > Lagging(약세)

## Archetypes

Dominant Compounder(Quality↑RS↑) · Emerging Leader(RS↑Momentum↑) · Fallen Leader(RS↓Momentum↓=후반부) · Turnaround(Quality↑RS개선=관찰대상) · Value Trap(Quality↑RS↓=시장 미인정)

## Quality·Expectation와의 3축 교차

Quality(현실)×Expectation(기대)×RS(행동) — Quality는 다른 두 모듈과 각각 Strong Compounder/Value Trap/Speculative Momentum 같은 조합을 만든다. **RS는 "행동"을 측정하는 유일한 축.**

## Veto Rules

RS=Breaking → Long 금지 / RS·Momentum 동시약세 → Conviction 제한 / Sector RS 약세 → 포지션 축소

## Limitations

"왜 강한지"는 설명 못함. **"Late Leader" 현상(강한 RS가 영구적 우위를 의미하지 않음)이 자주 발생한다고 명시**(§35-19) — RS 단독 추종의 위험을 자체 경고하고 있다.

## Output Schema

```json
{"state":"Leader","transition":"Improving","strength":4,"confidence":0.88,
 "narrative":"시장 및 섹터 대비 강한 상대성과를 기록하며 리더십이 강화되고 있다.",
 "risks":["모멘텀 둔화","Participation 약화"]}
```

## ✅ Sector Engine과의 데이터 계약 — 해결

Sector Engine §21과 Stock Engine §35는 "Sector RS"라는 동일한 이름의 중간 계층을 공유한다(§35-6). 매크로↔Sector 모듈화와 같은 원칙(`../sector_engine/21_relative_strength.md` "Macro Engine과의 데이터 계약")을 한 단계 더 적용한다: **3계층 RS 중 Sector RS만 §21의 출력을 그대로 재사용**하고, 본 모듈은 §21에 없는 Market RS(vs SPY/QQQ)와 Peer RS(동종기업 내 위치)만 새로 계산한다.

| 구성 | 담당 | 비고 |
|---|---|---|
| Market RS | Stock §35(신규) | §21에 없는 축 |
| Sector RS | **Sector Engine §21 출력 재사용** | 새로 계산하지 않음 |
| Peer RS | Stock §35(신규) | §21에 없는 축(동종기업 비교는 섹터 단위보다 세밀) |
