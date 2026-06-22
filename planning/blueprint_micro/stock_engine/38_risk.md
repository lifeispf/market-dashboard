# Risk (§38)

> 원본: `micro Ideation/38_risk.md.pdf` | Fundamental Layer | **전 시간축(T0~T3) 최중요, 전체 Stock Engine 최강 Veto**

## 핵심 질문

무엇이 틀릴 수 있는가? 손실은 얼마나 커질 수 있는가? 무엇이 투자 가설을 무효화하는가?

## 설계 철학 — 핵심

"투자의 목표는 수익 극대화가 아니라, **치명적 손실을 피하면서 확률적 우위를 반복하는 것**." Risk는 Stock Intelligence Engine에서 가장 강력한 Veto 권한을 가진다.

## 6개 하위축

Business Risk(매출/고객 집중도, 경쟁압력, 기술붕괴) · Financial Risk(Net Debt, Interest Coverage, Liquidity, Cash Burn) · Execution Risk(가이던스 신뢰도, 마진 안정성, 경영진 신뢰도) · Price Risk(ATR, HV, Drawdown, MA거리) · Event Risk(실적/FDA/신제품/규제/소송 — **Binary** 등급 존재) · Macro Risk(금리/FX/원자재/섹터 노출)

## Composite State

"점수 평균이 아니다 — **가장 약한 고리가 중요하다**"(§38-11, 명시적 약한고리 원칙). Low Risk★★★★★ ~ Extreme Risk★

## Position Sizing 원칙 — 본 모듈의 가장 중요한 설계 결정

**포지션 크기는 Conviction이 아니라 Risk에 의해 결정된다**(§38-16). Conviction 높음+Risk 높음 → 작은 포지션 / Conviction 보통+Risk 낮음 → 큰 포지션.

## Invalidation 원칙

"무효화 조건이 없는 투자는 투자가 아니라 희망이다"(§38-21). 예: 50MA 이탈, 가이던스 하향, Participation 붕괴, RS 약화, Catalyst 소멸 → 재평가 트리거.

## Veto Rules

Extreme Risk → Long 제한 / Binary Event → 포지션 크기 제한 / Financial Distress → Strong Up 금지 / Event Risk+High Volatility → Conviction 상한 제한 / Tail Risk 증가 → Risk Budget 축소

## Output Schema

```json
{"state":"Moderate Risk","transition":"Stable","strength":3,"confidence":0.88,
 "narrative":"재무구조는 건전하지만 실적 발표 이벤트 리스크가 존재한다.",
 "risks":["실적 변동성","밸류에이션 부담"]}
```

## 🔶 Opus 검토

- Position Sizing 원칙(§38-16)은 Stock Engine 8개 모듈 중 유일하게 **실행(execution) 레이어로 곧장 이어지는 구체적 규칙**이다. 사실상 이것이 "Strategy Engine"이 담당해야 할 로직의 일부를 Risk 모듈이 선점한 것처럼 보인다 — Strategy Engine이 설계될 때 이 원칙과의 역할 분담(Risk가 정성적 한도를 주고 Strategy가 수치화하는가?)을 명확히 할 필요. (`../90_open_questions.md` A-3번)
- "가장 약한 고리" 원칙은 좋은 설계 직관이지만 6개 하위축 중 어느 것이 "가장 약한"지 판정하는 알고리즘(단순 min()? 가중치?)이 명시되지 않았다.
