# Sector Momentum (§25)

> 원본: `micro Ideation/25_sector_momentum.pdf`

## 핵심 질문

"강한가?"가 아니라 "강해지고 있는가?" — RS와 짝을 이루는 **속도(velocity) 계층**.

## 설계 철학

Momentum은 방향이 아니라 변화를 측정한다 → 현재 가장 강한 섹터보다 **앞으로 강해질 섹터**를 찾는 데 유용하다. (예: Technology RS매우강함+Momentum둔화 = Late Leader / Industrials RS보통+Momentum강함 = Emerging Leader). §25-15는 "Momentum은 미래의 RS를 선행한다"고 명시하며, Sector Engine 안에서 **가장 예측적 성격이 강하다고 자체 평가**한다.

## 지표

Price Momentum(1/3/6M 수익률 변화율), RS Momentum(RS 변화 속도), ROC, MA Slope(20/50), MACD, RSI Trend(과열 여부), Acceleration(2차 변화율)

## 산출 구조

- **State**: Explosive / Accelerating / Stable / Decelerating / Negative
- **Transition**: Strengthening / Stable / Weakening / Reversing

## 핵심 충돌 패턴 (RS×Momentum — Sector Engine 핵심 듀얼 축)

| RS | Momentum | 해석 |
|---|---|---|
| ↑ | ↑ | Strong Leader |
| ↑ | ↓ | Late Cycle Leader(후반부) |
| ↓ | ↑ | Emerging Leader(차기 리더 후보) |
| (Rotation↑ 동반) | ↑ | Bull Expansion |
| Breadth↓ | ↓ | 붕괴 위험 |

## Output Schema

```json
{"state":"Accelerating","transition":"Strengthening","strength":4,"confidence":0.83,
 "narrative":"상대강도와 가격 추세가 동시에 강화되고 있다.",
 "risks":["Momentum 둔화","Breadth 악화"]}
```

## Limitations

왜 변화가 발생하는지는 설명 못함, 단기 가격변동에 민감해 노이즈가 많음 → RS/Breadth/Participation/Catalyst와 함께 해석.

## 🔶 Opus 검토

"Momentum이 미래 RS를 선행한다"(§25-15)는 주장은 **검증되지 않은 자기서술**이다. 기존 매크로 엔진이 거친 이벤트스터디·walk-forward 검증(`기획안_v3.md` §A)과 같은 실증 절차 없이 "가장 예측적인 모듈"이라 단정하는 것은 과신 위험 — 매크로 엔진이 v2→v3에서 겪은 것과 동일한 교정이 Sector Engine에도 필요할 수 있다. (`90_open_questions.md` B-6번)
