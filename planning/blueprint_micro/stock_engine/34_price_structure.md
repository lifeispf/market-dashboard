# Price Structure (§34)

> 원본: `micro Ideation/Price Structure.pdf` (34_price_structure.md) | Price Layer | **T0~T1 최중요, Strategy Engine과 가장 직접 연결**

## 핵심 질문

지금 어디에서 사고, 어디에서 틀렸다고 판단할 것인가? ("무엇을 살까"가 아니라 "**언제** 살까")

## 설계 철학

좋은 기업+강한 RS가 있어도 위치(가격 구조)가 나쁘면 좋은 투자 대상이 아니다.

## 5개 하위축

| 축 | 내용 | State |
|---|---|---|
| Trend | 20/50/200MA 위/기울기, Higher High-Higher Low | Strong Uptrend ~ Breakdown |
| Base | Flat/Cup&Handle/Consolidation/Ascending, Stage 1~4 | Constructive/Neutral/Weak |
| Breakout | 신고가+Volume확인+ATR확장+RS신고가 | Confirmed/Early/Neutral/Failed |
| Volatility | ATR, HV, Gap Risk, Earnings Risk | Low/Normal/High/Extreme |
| Risk/Reward | 지지선·무효화 거리, Expected Upside, R Multiple | Excellent/Good/Neutral/Poor |

## Composite State

Ideal Setup★★★★★ > Constructive★★★★ > Neutral★★★ > Extended★★ > Broken★

## Archetypes

Early Stage Breakout(Base+RS↑+Participation↑=초기강세) · Trend Leader(보유구간) · Extended Winner(추세는 강하나 위치 나쁨=신규진입 비추천) · Failed Breakout(주의) · Stage 4 Decline(회피)

## Veto Rules

Structure=Broken → Long 금지 / Failed Breakout → Conviction 제한 / Stage4 → 회피 / Extreme Volatility → 포지션 축소

## 타 모듈과의 관계

RS(무엇을 살지) × Structure(언제 살지) × Participation(Breakout 진위 확인)의 삼각관계. Structure↑+Participation↓=False Breakout, Base+Participation↑=Institutional Accumulation.

## Output Schema

```json
{"state":"Constructive","transition":"Improving","strength":4,"confidence":0.84,
 "narrative":"건전한 베이스를 형성하며 돌파 가능성이 높아지고 있다.",
 "risks":["Breakout 실패","50일선 이탈"]}
```

## 🔶 Opus 검토

없음(자기완결적). Strategy Engine(다음 레이어)이 본 모듈의 Risk/Reward·무효화조건을 어떻게 실제 진입/사이징 로직으로 변환하는지가 정의되어 있지 않다 — `../90_open_questions.md` A-3번(Strategy Engine 부재) 참조.
