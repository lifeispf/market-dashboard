# Expectation (§32)

> 원본: `micro Ideation/32_expectation.md.pdf` | Market Layer | **T1~T2에서 중요도 최고**

## 핵심 질문

시장은 무엇을 기대하며, 그 기대는 상승/하락 중인가? Surprise 가능성은?

## 설계 철학 — 핵심

주가는 **절대 수준이 아니라 기대의 변화**에 반응한다. (매우 좋은 기업+매우 높은 기대 → 실적 Beat해도 주가 하락 / 평범한 기업+매우 낮은 기대 → 실적 Beat 시 주가 상승)

## 5개 하위축

Revision(EPS/매출/EBITDA/목표가의 30·90·180일 수정 방향) · Surprise History(최근 8분기 EPS/매출/가이던스 Beat율, Post-Earnings Return) · Guidance(Raise/Maintain/Cut + Forward Commentary) · Consensus Positioning(Buy비율/목표가 프리미엄/과열 여부) · Estimate Dispersion(애널리스트 추정치 분산=불확실성)

## Composite State / Transition

State: Very Positive/Positive/Neutral/Negative/Very Negative · Transition: Improving/Stable/Weakening/Breaking

## Archetypes

Positive Revision Story(초기강세) · Consensus Darling(과열위험) · Skeptical Winner(Revision↑Consensus↓=Upside Potential) · Fallen Angel(Quality↑Expectation↓=관찰대상) · Consensus Collapse(위험증가)

## Quality와의 관계 (Stock Engine 최중요 교차축)

| Quality | Expectation | 결과 |
|---|---|---|
| ↑ | ↑ | Compounder |
| ↑ | ↓ | **Value Trap** |
| ↓ | ↑ | **Speculative Story** |
| ↓ | ↓ | Weak |

> "실제 투자 기회의 대부분은 Quality와 Expectation의 불일치에서 발생한다"(§32-15) — 본 엔진 전체에서 가장 단정적인 주장 중 하나.

## Veto Rules

Revision Collapse → Conviction 감소 / Guidance Cut → Strong Up 금지 / Estimate Dispersion 급증 → 포지션 크기 제한 / 연속 Negative Surprise → 리스크 증가

## Output Schema

```json
{"state":"Positive","transition":"Improving","strength":3,"confidence":0.84,
 "narrative":"EPS와 매출 추정치가 지속적으로 상향되고 있으며 가이던스 역시 개선되고 있다.",
 "risks":["기대 과열","실적 실망 가능성"]}
```

## ✅ 데이터 소싱 — 해결

Estimate Revision·Guidance·Analyst Dispersion은 유료 컨센서스 벤더(Refinitiv I/B/E/S, FactSet 등) 없이도 Finnhub/FMP 무료티어 + SEC EDGAR(가이던스 정형 수치)로 1차 충당 가능하도록 재정리했다. 상세 소스 매핑은 `../data_sourcing.md` "§32 Expectation" 참조(`../90_open_questions.md` C-9 해결).
