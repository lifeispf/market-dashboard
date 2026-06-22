# Sector Rulebook (§29)

> 원본: `micro Ideation/29_sector_rulebook.md.pdf`
> Sector Intelligence Engine의 **해석 계층(interpreter)** — §21~26 6개 모듈을 종합해 투자적 의미를 생성하는 "두뇌"

## 출력

6축(RS/Breadth/Participation/Rotation/Momentum/Catalyst)의 상태를 해석하여 **Direction(Strong Up~Strong Down) · Strength(0~4) · Conviction(0~1) · Narrative · Invalidation(Risks)** 을 생성한다. 기존 매크로 엔진의 §15 "방향·강도 루브릭"과 정확히 같은 산출 철학(점수 합산 금지, 불일치=정보)을 공유한다.

## 모듈 우선순위 (기본값, 시장환경에 따라 가변)

1. Relative Strength → 2. Momentum → 3. Breadth → 4. Participation → 5. Catalyst → 6. Rotation

## 핵심 원칙

- **Alignment(정렬)**: 여러 모듈이 같은 방향을 가리킬수록 Conviction이 증가한다. (예: RS↑Momentum↑Breadth↑Participation↑ → 높은 확신)
- **Conflict(충돌)**: 모듈 간 불일치는 노이즈가 아니라 **가장 중요한 정보**이며, 후반부/전환점을 의미할 수 있다.

## Primary Patterns (10종, A~J)

| 패턴 | 조합 | 해석 |
|---|---|---|
| A. Strong Leader | RS↑Momentum↑Breadth↑Participation↑Catalyst↑ | Strong Up, Conviction Very High |
| B. Emerging Leader | RS↓Momentum↑Catalyst↑ | 차기 주도 섹터 후보 |
| C. Healthy Expansion | Breadth↑Participation↑ | 건강한 상승 |
| D. Late Leader | RS↑Momentum↓ | 추세 후반부 |
| E. Mega-cap Dependence | RS↑Breadth↓ | 소수 종목 의존 |
| F. False Leadership | RS↑Participation↓ | 거래량 미확인 |
| G. Early Rotation | Rotation↑Momentum↑ | 초기 상승 |
| H. Structural Winner | Catalyst↑RS↑ | 장기 주도 가능성 |
| I. Weak Expansion | Breadth↑Participation↓ | 확산은 있으나 힘 부족 |
| J. Breakdown | RS↓Momentum↓Participation↓ | 회피 구간 |

## Veto Rules

V1 Momentum Collapse → Strong Up 금지 / V2 Participation Breakdown → Conviction 상한 제한 / V3 Catalyst Reversal → Strength 감소 / V4 Broad Breadth Collapse → 위험 증가

## Cycle Patterns

Early(Momentum↑Catalyst↑Rotation↑, Breadth는 아직 보통이어도 정상 — false negative 주의) / Late(RS↑Momentum↓Breadth↓ → 대형주 집중·위험 증가)

## Output Schema

```json
{"direction":"strong_up","strength":4,"conviction":0.89,"lead_pattern":"Strong Leader",
 "narrative":"강한 상대강도와 모멘텀이 지속되고 있으며, Breadth와 Participation이 이를 지지하고 있다.",
 "risks":["Momentum 둔화","Breadth 악화","Catalyst 약화"]}
```

## Limitations (원문 명시)

"출력은 확률적 우위를 의미하며 미래 가격을 예측하는 것이 아니다. 새로운 시장 구조 변화가 발생하면 패턴은 지속적으로 수정되어야 한다."

## ✅ 신뢰도(confidence) 정책 — 결정 (2026-06-21)

`90_open_questions.md` B-6 해결. 본 Rulebook의 패턴 A~J·Veto V1~V4는 기존 매크로 §15 루브릭과 같은 "충돌 카탈로그" 사상이지만, 이벤트스터디·walk-forward 같은 실증 검증을 아직 거치지 않았다. 매크로 엔진이 v3에서 도입한 "확률 상한 0.6, expose_only_if_backtested" 검증 게이트(`기획안_v3.md` §4)는 **충분한 트레이드/결과 데이터가 누적된 뒤 별도 단계로 추진**하기로 결정했다 — 지금 당장 같은 게이트를 강제하지 않는다. 단, Output Schema의 `conviction` 값은 그 전까지 "규칙 기반 휴리스틱(정렬 정도를 나타내는 랭킹 신호)"로 취급하며 실제 확률로 해석하지 않는다. 정책 전문은 `../stock_engine/39_rulebook.md` §8 참조(Stock Engine과 정책 공유).

## ✅ §39 인터페이스 — 해결

`../stock_engine/39_rulebook.md`가 작성되어, 본 Rulebook의 출력(Direction/Strength/Conviction)을 Stock Engine이 어떻게 소비하는지 §39 "5. Sector → Stock 인터페이스"에 구체 규칙으로 정의했다(Sector Breaking → Stock Conviction 강제 하향 등).

## 🔶 Opus 검토 (잔존)

패턴 A~J·Veto V1~V4 자체의 실증 검증(이벤트스터디·walk-forward)은 여전히 미수행 상태다 — 위 정책 결정은 "지금 강제하지 않는다"는 결정이며 "영구히 안 한다"는 결정이 아니다. 충분한 데이터가 쌓이면 재검토 대상.
