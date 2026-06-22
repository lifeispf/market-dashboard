# Sector Relative Strength (§21)

> 원본: `micro Ideation/Sector Relative Strength.pdf` (21_sector_relative_strength.md)
> Sector Engine의 **중심축** — 다른 모듈은 이를 검증/반박하는 역할(§21-14)

## 핵심 질문

지금 시장을 주도하는 섹터는 어디이며, 다음 주도 섹터가 될 가능성이 높은 곳은 어디인가?

## 설계 철학

절대 수익률이 아니라 **상대적 우위**가 중요하다. (SPY +10%/XLK +18% → 기술주 강세. SPY −15%/XLV −8% → 헬스케어는 하락장에서도 상대적으로 강함.)

## 데이터

- 미국 섹터 ETF: XLK/XLF/XLY/XLI/XLE/XLV/XLP/XLU/XLB/XLRE/XLC, 벤치마크 SPY/QQQ
- 한국: KODEX/TIGER 섹터 ETF(반도체·자동차·2차전지·헬스케어·은행·보험·조선), 벤치마크 KOSPI/KOSDAQ
- 다중 시간축 동시 관찰: 1M(단기)/3M(중기)/6M(추세)/12M(장기)

## 산출 구조

- **State**: Leader / Emerging / Average / Lagging / Broken
- **Transition**: Improving / Stable / Weakening / Breaking (State보다 중요)
- RRG(Relative Rotation Graph) 4분면: Leading(강RS+강Momentum) / Improving(약RS+강Momentum) / Weakening(강RS+약Momentum) / Lagging(약RS+약Momentum)
- 보조지표: RS Momentum, RS Acceleration, RS Slope, Distance From RS MA

## 핵심 충돌 패턴

| 패턴 | 의미 |
|---|---|
| RS↑ + Breadth↓ | Mega-cap 집중, 후반부 가능성 |
| RS↑ + Participation↓ | 가짜 강세 |
| RS↑ + Catalyst 없음 | 지속성 의문 |
| RS↓ + Momentum↑ | 반등(차기 리더) 가능성 |

## State × Transition 해석

Leader+Improving=초기상승(High Conviction) / Leader+Stable=성숙한 추세(Medium) / Leader+Weakening=후반부(경계) / Lagging+Improving=차기 리더 후보(관찰) / Lagging+Breaking=회피 대상

## 타 모듈과의 관계

RS → Breadth(건강한가?) → Participation(돈이 들어오나?) → Catalyst(왜?) → Rulebook(종합). "다른 모듈은 RS를 검증하거나 반박하는 역할을 수행한다."

## Output Schema

```json
{"state":"Leader","transition":"Improving","strength":4,"confidence":0.82,
 "narrative":"기술 섹터의 상대강도가 시장 대비 지속적으로 개선되고 있다.",
 "risks":["Breadth 약화","Participation 둔화"]}
```

## Limitations

"무엇이 강한가"는 설명하지만 "왜 강한가"는 설명하지 못한다 → Catalyst/Participation/Breadth와 함께 해석 필수.

## ✅ Macro Engine과의 데이터 계약 — 중복 해소 (결정 2026-06-21)

`90_open_questions.md` B-5 해결. RRG 원시 계산(RS-Ratio×RS-Momentum)은 기존 매크로 엔진의 `scoring.py` §5-2 RRG 함수(`기획안.md` §5-2, 단순화 JdK 공식)를 **유일한 계산 출처**로 채택한다. Sector Engine §21은 이를 재계산하지 않고 입력으로 받아, 매크로 엔진에 없는 것만 추가한다.

| 계층 | 담당 | 산출 |
|---|---|---|
| 매크로 엔진(기존, 변경 없음) | RS-Ratio/RS-Momentum **단일 윈도우** 계산 + 4분면 스냅샷 | 크로스 내러티브 배지용 "지금 1등 섹터"(leading/improving 1개씩) |
| Sector Engine §21(본 모듈, 신규) | 동일 함수를 **다중 시간축**(1M/3M/6M/12M)으로 재호출 + Leader/Emerging/Average/Lagging/Broken **State** 분류 + Transition(지속성) 판정 + 한국 KODEX/TIGER 확장 | 섹터별 정밀 진단 |

**데이터 계약**: 매크로 엔진은 `{sector_ticker, rs_ratio, rs_momentum, window}`를 노출하고(구현 시 `scoring.py`의 RRG 계산을 공용 모듈로 분리해 두 레이어가 import), Sector Engine §21은 이를 여러 `window` 값으로 호출해 자체 State/Transition 레이어를 그 위에 얹는다. 같은 공식을 두 곳에서 따로 구현하지 않는 것이 핵심 — 계산 코드는 하나, 해석 레이어는 둘.

## 🔶 Opus 검토 (잔존)

State 경계(예: 몇 %ile RS부터 "Leader"인지)에 대한 정량 기준이 명시되지 않음 — 구현 전 정량화 패스 필요(전 모듈 공통 이슈, `90_open_questions.md` D-12번).
