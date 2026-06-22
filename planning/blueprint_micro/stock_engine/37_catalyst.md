# Stock Catalyst (§37)

> ⚙️ **본 파일은 원본 PDF가 아니라 Claude가 새로 설계한 스펙이다** (2026-06-21, 사용자 승인 하에 작성·`90_open_questions.md` A-1 해결). 원본 결손 경위는 하단 "결손 경위"에 보존. Fundamental Layer | **T0~T1 중요, T3 거의 무관**

## 결손 경위 (보존)

`micro Ideation/` 폴더에는 §37 본문이 없었다. `30_stock_engine.md.pdf`가 모듈 아키텍처·Components 목록에 "37 Catalyst"를 명시하고, 31/32/33/34/35/36/38 7개 형제 문서가 전부 이를 인용했지만 실제 스펙은 부재했다. 아래는 그 인용 패턴과 Sector Catalyst(§26) 구조를 토대로 새로 설계한 내용이다.

## 핵심 질문

이 종목은 지금 왜 움직이는가? 다음 촉매는 무엇이고 언제 오는가?

## 설계 철학 — 핵심

RS(§35)·Participation(§36)이 "무엇이 움직이는가"를 보여준다면, Catalyst는 "왜, 그리고 언제 또"를 답한다. **모든 촉매를 이 모듈에서 새로 계산하지 않는다** — Sector Catalyst(§26)가 이미 계산한 섹터 공통 촉매(구조적/순환적/정책)는 **상속**받고, §37은 ① 그 섹터 촉매에 이 종목이 얼마나 노출되어 있는지(exposure)와 ② 이 종목만의 고유 이벤트만 새로 계산한다. 이는 Sector Engine §21/§24가 매크로 엔진의 RRG/로테이션을 재계산하지 않고 상속하는 것과 동일한 모듈화 원칙이다(`../sector_engine/21_relative_strength.md` 참조).

## 데이터 계약 — §26 Sector Catalyst와의 분리

| 계층 | 담당 | 산출 |
|---|---|---|
| Sector Catalyst(§26, 기존) | 구조적/순환적/정책/이벤트 촉매를 섹터 단위로 분류 | `{state, transition, strength}` — 변경 없이 그대로 입력받음 |
| Stock Catalyst(§37, 본 모듈) | 위 출력을 상속 + 이 종목의 섹터노출도(exposure, 정성평가) 추정 + 기업 고유 이벤트(실적/가이던스/제품/M&A/경영진/소송/승인) 신규 계산 | 종목 단위 Catalyst State/Transition |

기업 고유 이벤트는 §31 Quality(현실)·§32 Expectation(기대) 그 자체와 다르다 — Catalyst는 "무엇이 언제 일어났는가"만 답하고, 그 사건이 좋은 소식인지는 Expectation이, 사건이 구조를 바꾸는지는 Quality가 판단한다.

## 데이터 소스

News(기업 고유), SEC 8-K/10-Q 공시, 실적 발표 일정·가이던스(보도자료 정형 수치), 제품/임상/승인 캘린더(해당 업종), M&A·경영진 변경 공시, §26 Sector Catalyst 출력(상속) — 텍스트 소싱 상세는 `../data_sourcing.md` 참조.

## 지표

- **Catalyst Calendar**: 다음 예정 이벤트와 날짜(실적발표일, 승인심사일, Investor Day 등) — Known/Scheduled 여부
- **Catalyst Type**: Binary(결과가 크게 갈림 — 임상결과/승인/대형계약) vs Continuous(점진적 — 가이던스 추세)
- **Catalyst Outcome**: Confirmed Positive / Confirmed Negative / Pending / Faded
- **Sector Inheritance**: §26 출력 원본 그대로(가공 없이 전달)
- **Decay**: 촉매 발생 후 가격 반응이 즉시 소화되는지 지속 드리프트하는지

## State / Transition

- **State**: No Catalyst(촉매 없음) / Pending(예정 촉매 대기) / Active(발생, 시장 소화 중) / Faded(효과 소멸)
- **Transition**: Emerging(신규 부상) / Stable / Decaying(약화) / Invalidating(테제 무효화 방향 — 예: 가이던스 철회)

## State × Transition 해석

Active+Emerging=신규 촉매 막 발생(고변동성, 방향 미확정) / Pending+Stable=예정 이벤트 대기(§38 Event Risk와 직결) / Faded+Decaying=촉매 소진(차익실현 압력) / Active+Invalidating=확인된 악재(즉시 재평가 대상)

## 핵심 충돌 패턴

| 패턴 | 의미 |
|---|---|
| Catalyst Pending(Binary) + Positioning Crowded | 양방향 변동성 위험 — 실패 시 급락 |
| Catalyst Confirmed Positive + RS 무반응 | 이미 선반영(Expectation 확인 필요) |
| Catalyst 없음 + Price 급등 | 설명되지 않는 움직임(Positioning 정보 비대칭 의심) |
| Sector Catalyst↑ + Stock Catalyst 없음 | 섹터 수혜 베타만 존재, 고유 촉매 부재(지속성 의문) |
| Catalyst Invalidating + Quality Elite | 구조 vs 이벤트 분리 필요(단기 충격이 장기 테제를 깨는지 판단) |

## Relationship With Other Modules

§26(상속 베이스) · §32 Expectation("그게 좋은 소식이었는가") · §38 Risk(Catalyst의 Binary 분류가 Event Risk 서브축의 입력값 — 이중 집계 방지를 위해 거부권은 §38/§39에서만 행사)

## Output Schema

```json
{"state":"Pending","transition":"Stable","strength":2,"confidence":0.6,
 "narrative":"3주 후 실적 발표가 예정되어 있으며, 섹터 차원의 구조적 촉매가 이어지고 있다.",
 "risks":["가이던스 불확실성","섹터 촉매 의존도"],
 "next_catalyst_date":"T+21","catalyst_type":"continuous"}
```

> confidence를 0.6으로 예시한 것은 의도적이다 — 본 모듈은 검증을 거치지 않은 신규 설계이므로, 다른 sourced 모듈의 예시값(0.8~0.9대)을 그대로 따르지 않고 보수적으로 낮춰 "비검증" 신호임을 스키마 자체로 드러낸다. 상세 정책은 `39_rulebook.md` "신뢰도 정책" 참조.

## Time Horizon

T0(이벤트 당일 반응) 최중요 / T1(이벤트 후 드리프트) 중요 / T2(다음 촉매까지 거리) 보통 / T3 거의 무관 — 촉매는 본질적으로 단·중기 신호.

## Veto Rules

- Binary Catalyst Pending + 미해결 → Conviction 상한(§38 Event Risk와 동일 조건 공유, 이중 집계 방지 위해 최종 거부권은 §39에서 한 번만 적용)
- Catalyst Invalidating 확인 → 기존 강세 신호 무효화 권고(최종 거부권은 §38/§39 행사)

## Limitations

기업 고유 촉매 분류는 텍스트(뉴스/공시) 처리가 필요해 §26과 동일한 NLP 의존 한계를 공유한다. 이항 이벤트의 **결과 예측은 범위 밖** — 타이밍과 분류만 제공한다. exposure(섹터 촉매 노출도) 추정은 현재 정성적 판단이며 정량화는 전 모듈 공통 후속 과제(`../90_open_questions.md` D-12)다.

## Final Objective

이 종목이 왜 움직였는지, 다음에 무엇을 봐야 하는지를 추적 가능한 형태로 제공한다 — 예측이 아니라 **인과 추적(causal tracing)**이 목적이다.
