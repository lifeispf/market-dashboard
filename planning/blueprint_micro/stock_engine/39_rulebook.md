# Stock Rulebook (§39)

> ⚙️ **본 파일은 원본 PDF가 아니라 Claude가 새로 설계한 스펙이다** (2026-06-21, 사용자 승인 하에 작성·`90_open_questions.md` A-2 해결). Stock Intelligence Engine 전체를 종합하는 해석 계층(interpreter) — §29 Sector Rulebook의 형식을 차용해 Stock Engine의 3계층(Fundamental/Market/Price) 구조에 맞게 재설계했다. 원본 결손 경위는 하단 "결손 경위"에 보존.

## 결손 경위 (보존)

`30_stock_engine.md.pdf`는 §39에 최종 해석을 명시적으로 위임했으나("Stock Engine 자체는 최종 결론을 내리지 않는다... 최종 해석은 §39 Stock Rulebook에서 수행한다", 30-11) 실제 문서는 폴더에 없었다. §29 Sector Rulebook과 달리 모듈 우선순위 재조정 규칙, Alignment/Conflict 적용 로직, 패턴 카탈로그, Veto Rules, Cycle 패턴, Narrative 예시, Output Schema가 전부 부재했다. 아래는 §29의 형식을 8개 모듈(§31~38)·3계층 구조에 맞게 새로 빌드한 것이다.

## 핵심 질문

Fundamental·Market·Price 3계층 8개 모듈(§31~38)의 출력을 어떻게 종합해 하나의 투자 판단(Direction/Strength/Conviction/Narrative/Invalidation/Position Size Hint)으로 만드는가?

## 설계 철학

§29와 동일 — **점수를 합산하지 않는다. 불일치(Conflict)가 신호다.** 추가 원칙: Stock Engine은 계층(Layer) 자체에도 시간축에 따른 우선순위가 있다 — 모든 Horizon에서 8개 모듈을 동일 가중치로 보지 않는다.

## 1. 가중치 축 — Horizon별 계층 우선순위

> 이 표는 "중요도"만 다룬다. "거부권"은 별도 축(§2)이다 — 기존 §30 우선순위 표가 두 축을 한 표에 섞어 혼란을 유발했던 문제(`../90_open_questions.md` E-15)를 여기서 분리한다.

| Horizon | 1순위 계층 | 2순위 | 3순위 |
|---|---|---|---|
| T0 (1~5일) | Price (Structure·Participation) | Market (Catalyst 타이밍) | Fundamental |
| T1 (1~6주) | Price (RS·Participation) | Market (Positioning·Catalyst) | Fundamental |
| T2 (1~6개월) | Market (Expectation) | Fundamental (Quality) | Price |
| T3 (1~2년) | Fundamental (Quality) | — | Market·Price는 참고용 |

## 2. 거부권(Veto) 축 — 가중치와 분리

Risk(§38)는 모든 Horizon에서 가중치 순위와 무관하게 거부권을 가진다. "이 모듈이 얼마나 중요한가"와 "이 모듈이 다른 신호를 무효화할 수 있는가"는 다른 질문이다.

| 거부 모듈 | 조건 | 효과 |
|---|---|---|
| Risk(§38) | Extreme Risk | Conviction 전체 상한(모든 계층 무시) |
| Risk(§38) | Invalidation 조건 발생 | 기존 판단 즉시 폐기, 재평가 강제 |
| Quality(§31) | Broken (T2~T3 한정) | 장기 강세 신호 전부 무효 |
| Participation(§36) | Breaking (T0~T1 한정) | Breakout·단기 강세 신호 무효 |
| Catalyst(§37) | Binary Pending 미해결 | Conviction 상한(이벤트 종료까지) — §38 Event Risk와 조건 공유, 이중 집계 방지 위해 여기서 1회만 적용 |

## 3. 종합 절차 — 2단계 집계

1. **계층 내부 종합**: 같은 계층 안에서 Alignment/Conflict 판정 (예: Fundamental 내부 Quality↑+Risk↓=정상, Quality↑+Catalyst Invalidating=내부 충돌 → 계층 자체의 신뢰도 하향)
2. **계층 간 종합**: 3계층 결과를 §1의 Horizon별 가중치로 교차 해석 (예: T2에서 Fundamental Bullish + Market Bearish = Value Trap 패턴)

## 4. Primary Patterns (10종, A~J)

| 패턴 | 조합 | 해석 |
|---|---|---|
| A. Full Alignment Bull | Quality↑ Expectation↑ Positioning Under-owned Price Leader | 최고 확신 Long |
| B. Value Trap | Quality↑ Expectation↓ (§32 매트릭스 상속) | 회피 — 좋은 회사, 비싼 기대 |
| C. Crowded Momentum | Price Leader + Positioning Crowded + Expectation Stretched | 후반부, 반전 취약 |
| D. Quiet Accumulation | Quality 개선 + Positioning Under-owned + Price 베이스구축(RS 미확인) | 초기 기회, 확인 약함 |
| E. Broken Thesis | Catalyst Invalidating + Risk Invalidation 발생 | 즉시 회피(Risk 거부권 발동) |
| F. Sector Drag | Stock 펀더멘털 양호 + Sector Rulebook(§29) Weakening/Breaking | 섹터발 역풍, Conviction 강제 하향 |
| G. Binary Event Pending | Catalyst Pending(Binary) + Positioning 집중 | Conviction 상한(이벤트 종료까지) |
| H. Story Without Numbers | Expectation Stretched + Quality Weak/Speculative | 고위험 스토리주 |
| I. Mean Reversion Setup | Price Oversold/Breaking + Quality Elite/Stable + Positioning Capitulation | 역발상 기회(확인 필요) |
| J. Distribution Top | Price Leader + Participation 감소 + Positioning Crowded 둔화 | 분배·천장 패턴 |

## 5. Sector → Stock 인터페이스 (상위 필터 원칙 명문화)

§29 Sector Rulebook 출력(Direction/Strength/Conviction)을 다음 규칙으로 소비한다 — §30-12 "상위 필터" 원칙을 구체적 규칙으로 변환:

- Sector Direction = Strong Down, 또는 패턴 Breakdown(J) → Stock Conviction **1단계 강제 하향** (패턴 F 적용)
- Sector Direction = Strong Up + Conviction 높음 → Stock Conviction **상향 보너스**(단, Stock 자체 Veto가 없을 때만)
- Sector 출력 Neutral/부재 → 가중치 영향 없음

## 6. Cycle Patterns

- **Early-stage**: Quality 개선 중 + Positioning Under-owned + Price 베이스구축, Expectation 아직 낮음
- **Late-stage**: Quality Elite로 안정 + Expectation Stretched + Positioning Crowded + Price Extended

§29의 Early/Late Cycle 사상을 종목 단위로 재적용한 것이다.

## 7. Output Schema

```json
{"direction":"bullish","strength":3,"conviction":0.62,
 "lead_pattern":"Quiet Accumulation",
 "position_size_hint":"half",
 "narrative":"펀더멘털 개선과 낮은 기관 보유가 맞물려 있으나, 가격 구조의 확인은 아직 약하다.",
 "risks":["Price 확인 부족","Sector 모멘텀 의존"],
 "invalidation_conditions":["50일선 이탈","가이던스 하향","Sector Rulebook Breaking 전환"],
 "horizon":"T2"}
```

`position_size_hint`(full/half/quarter/avoid)는 신규 필드다. §38의 "포지션 크기는 Conviction이 아니라 Risk가 결정한다"(§38-16) 원칙을 Rulebook 출력에 명시적으로 반영한 것 — Strategy Engine이 아직 설계되지 않은 상태(`../90_open_questions.md` A-3)에서, 이 필드가 그 역할의 잠정 입력값을 제공한다. Strategy Engine이 실제로 설계되면 이 필드의 소유권을 이전할지 검토 필요.

## 8. 신뢰도(confidence/conviction) 정책 — 사용자 결정 반영

> Stock/Sector Engine 전체의 confidence·conviction 값은 현재 **규칙 기반 휴리스틱**(몇 개 모듈이 정렬되는가를 반영한 추정치)이며 실증 검증을 거치지 않았다. 매크로 엔진이 v3에서 도입한 이벤트스터디·walk-forward·base-rate 상한 0.6 규율(`기획안_v3.md` §4)과 같은 검증 게이트는 **충분한 트레이드/결과 데이터가 누적된 뒤 별도 단계로 추진하기로 결정**했다(2026-06-21, `../90_open_questions.md` B-6). 그 전까지 이 수치는 "정렬 정도를 나타내는 랭킹 신호"로만 취급하고 실제 확률로 해석하지 않는다. 계산 공식 자체(몇 개 모듈 정렬 시 몇 점인지)는 여전히 미정으로 남아 있다 — 이는 정책 결정과는 별개의 구현 과제다(`../90_open_questions.md` D-13).

## Limitations

패턴 카탈로그(§4)는 초기 설계로, §29와 마찬가지로 실거래 데이터 누적 후 재조정이 필요하다. 8개 입력 모듈 중 §37은 NLP 의존도가 높아 모듈별 입력 신뢰도가 균일하지 않을 수 있다. 본 Rulebook 자체도 신규 설계이므로 Sector Rulebook(§29, 원본 소싱)보다 한 단계 더 낮은 확신도로 취급해야 한다.

## Final Objective

"이 종목을 사야 하는가"가 아니라 "이 종목에 확률적 우위가 있는가, 있다면 얼마나 강하게·얼마나 확신을 갖고·무엇이 틀렸을 때 멈출 것인가"에 답한다.
