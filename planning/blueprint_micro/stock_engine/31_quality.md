# Quality (§31)

> 원본: `micro Ideation/31_quality.md.pdf` | Fundamental Layer 중심축 | **T2·T3에서 최강 Veto**

## 핵심 질문

좋은 사업/재무구조/수익성/지속가능한 성장을 가진 회사인가?

## 설계 철학 — 중요

Quality는 "좋은 기업"을 평가하지만 **"좋은 투자"를 평가하는 모듈이 아니다.** 필요조건이지 충분조건이 아니다(훌륭한 기업+높은 기대=비싼 주식, 평범한 기업+낮은 기대=좋은 투자기회일 수 있음).

## 4개 하위축

| 축 | 지표 | State |
|---|---|---|
| Growth | Revenue/EPS CAGR(3·5Y), EBITDA/영업이익 성장, 희석여부 | Exceptional/Strong/Average/Weak |
| Profitability | Gross/Operating/EBITDA Margin, ROIC, ROE, Incremental Margin | Elite/Strong/Average/Weak |
| Cash Generation | FCF Margin/CAGR/Conversion, Owner Earnings, Capex Intensity | Excellent/Strong/Average/Weak |
| Financial Health | Net Debt, D/E, Interest Coverage, Current/Cash Ratio, 만기구조 | Fortress/Strong/Average/Fragile |

## Composite State / Transition

State: Elite / Strong / Average / Weak / Broken · Transition: Improving/Stable/Weakening/Breaking (네 축의 평균이 아니라 해석을 통해 합성)

## Archetypes

Compounder(전축↑) · Asset Light Leader(수익성·FCF↑, Capex↓) · Hyper Growth(성장↑수익성↓=잠재력) · Mature Cash Machine(성장↓FCF↑=안정적) · Leveraged Story(성장↑부채↑=취약)

## 데이터

재무제표(IS/BS/CF), SEC Filings(10-Q/10-K/8-K), Earnings Transcript, 과거 펀더멘털, (보조)애널리스트 데이터

## Veto Rules

Quality=Broken → 모든 강세 신호 무효 / Financial Health=Fragile → 포지션 크기 제한 / FCF 붕괴 → Conviction 감소

## 타 모듈과의 관계

Quality(현실) × Expectation(기대)의 **불일치**에서 대부분의 실제 투자 기회가 발생한다(→ `32_expectation.md` 참조). Quality↑+RS↓=Value Trap, Quality↓+RS↑=Speculative Momentum.

## Output Schema

```json
{"state":"Elite","transition":"Stable","strength":4,"confidence":0.91,
 "narrative":"높은 성장성과 수익성, 강한 현금창출 능력을 보유하고 있다.",
 "risks":["마진 압박","성장 둔화"]}
```

## 🔶 Opus 검토

없음(자기완결적). 4개 하위축의 State 경계치(예: ROIC 몇 % 이상이 "Elite")가 미정인 점은 전 모듈 공통 이슈(`../90_open_questions.md` D번).
