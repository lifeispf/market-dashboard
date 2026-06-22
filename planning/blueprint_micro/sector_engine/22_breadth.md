# Sector Breadth (§22)

> 원본: `micro Ideation/22_sector_breadth.pdf`

## 핵심 질문

상승이 섹터 전체에서 발생하는가, 아니면 일부 초대형 종목만 끌어올리는가?

## 설계 철학

Relative Strength가 "누가 강한가"를 답한다면 Breadth는 "그 강세가 건강한가"를 답한다. 폭(Breadth)은 추세의 **질(Quality)**을 측정한다.

## 데이터

ETF 구성종목(SMH/XLK/XLF/XLI 등), OHLCV, 이동평균(20/50/200MA), 52주 신고가·신저가 DB

## 지표

% Above 20/50/200MA, New High Ratio, New Low Ratio, Advance/Decline Ratio, Equal-Weight Relative Strength(동일가중 vs 시총가중 비교), Market Cap Concentration

## 산출 구조

- **State**: Broad Leadership / Healthy / Narrow / Weak / Broken
- **Transition**: Expanding / Stable / Narrowing / Collapsing

## 핵심 충돌 패턴

| 패턴 | 의미 |
|---|---|
| RS↑ + Breadth↑ | 건강한 리더 |
| RS↑ + Breadth↓ | 집중 현상(Mega-cap Dependence), 후반부 가능성 |
| Breadth↑ + Participation↓ | 실제 자금 유입 부족 |
| Breadth↓ + Catalyst↑ | 일시적 현상 가능성(아래 Limitations 참조) |

## Divergence (조기 경고)

가격↑+Breadth↓ → 후반부 / 신고가↑+신고가종목수↓ → 내부 약화 / 지수↑+50MA위 비율↓ → 상승 피로

## 타 모듈과의 관계

Breadth(종목 수)와 Participation(자금 강도)은 서로 독립적인 축이다. 둘 다 ↑일 때가 "가장 건강한 상태"이며, Breadth↓+Participation↑은 대형주 집중을 뜻한다.

## Output Schema

```json
{"state":"Broad Leadership","transition":"Expanding","strength":4,"confidence":0.85,
 "narrative":"상승이 섹터 전반으로 확산되고 있다.",
 "risks":["거래량 둔화","Catalyst 소멸"]}
```

## Limitations

Catalyst가 강한 초기 국면에서는 일시적으로 Breadth가 약할 수 있다(false negative 주의) → RS/Participation/Catalyst와 함께 해석.

## 🔶 Opus 검토

본 모듈 자체는 비교적 자기완결적이다. 정량 임계치 미정(어느 %부터 "Broad Leadership"인지)은 전 모듈 공통 이슈로 `90_open_questions.md` D번에 일괄 기재했다.
