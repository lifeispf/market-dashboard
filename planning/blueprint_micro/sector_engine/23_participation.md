# Sector Participation (§23)

> 원본: `micro Ideation/23_sector_participation.pdf`

## 핵심 질문

지금의 움직임은 진짜인가, 단순 가격 상승일 뿐인가?

## 설계 철학

가격은 움직임을 보여주고, 거래량은 확신을 보여준다 — Participation은 그 움직임을 만든 자금의 강도를 설명한다.

## 데이터

OHLCV, 섹터 ETF 거래량, 동일가중 ETF(RSP/QQQE), Relative Volume(RVOL), (가능시) ETF/Fund Flow, Institutional Flow

## 지표

RVOL(현재거래량÷평균거래량), Volume Trend, OBV, CMF, Accumulation/Distribution, ETF Fund Flow(순유입/유출), Volume Confirmation(가격상승과 거래량 동반 여부)

## 산출 구조

- **State**: Strong Accumulation / Accumulation / Neutral / Distribution / Capitulation
- **Transition**: Improving / Stable / Weakening / Breaking

## 핵심 충돌 패턴

| 패턴 | 의미 |
|---|---|
| RS↑ + Participation↑ | 진짜 리더 |
| RS↑ + Participation↓ | 가짜 강세(False Leadership) |
| Breadth↑ + Participation↑ | 가장 건강한 상태 |
| Breadth↓ + Participation↑ | 대형주 집중 |
| Breadth↑ + Participation↓ | 확산되지만 힘 부족 |

## Divergence

가격↑+거래량↓ → 상승피로 / Breakout+Volume없음 → False Breakout / 신고가+OBV하락 → Distribution

## 타 모듈과의 관계

Breadth(몇 종목이 움직이나)와 Participation(얼마나 강하게 움직이나)은 서로 독립적인 두 축이다. RS를 검증하는 역할을 수행하며, Sector Engine에서 Breadth와 함께 가장 중요한 보조 모듈로 자체 평가된다.

## Output Schema

```json
{"state":"Accumulation","transition":"Improving","strength":4,"confidence":0.83,
 "narrative":"거래량과 자금 유입이 상승 추세를 지지하고 있다.",
 "risks":["거래량 둔화","상대강도 약화"]}
```

## 🔶 Opus 검토

없음 — 전 모듈 공통 이슈(정량 임계치, confidence 산식 미정)는 `90_open_questions.md` 참조.
