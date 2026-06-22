# Sector Catalyst (§26)

> 원본: `micro Ideation/26_sector_catalyst.pdf`

## 핵심 질문

왜 이 섹터가 강한가? 그 움직임은 구조적인가, 순환적인가, 일시적인가?

## 설계 철학

가격은 결과, Catalyst는 원인이다. **"Catalyst 없는 강세는 지속성이 낮다."** Sector Engine에서 가장 정성적(qualitative)이지만 가장 설명력이 높은 모듈로 자체 평가된다.

## Catalyst 분류 & 지속성 계층

| 유형 | 예시 | 지속성 |
|---|---|---|
| Structural | AI CAPEX(GPU/메모리/네트워킹/전력/쿨링), 클라우드 확장, 전력망/원전/EV/로보틱스/데이터센터, 국방예산, 인구구조 | ★★★★★ |
| Cyclical | 반도체 재고/ASP/CAPEX 사이클, 원자재(유가/구리/천연가스), 주택·신용·제조·소비 사이클 | ★★★★ |
| Policy | 금리, 재정정책, 관세, 규제완화, 산업지원정책, 세금정책 | ★★★ |
| Event | 실적발표, 가이던스 수정, 신제품 출시, M&A, 바이백, Investor Day, CEO 교체 | ★★ |

## 산출 구조

- **State**: Structural Tailwind / Positive / Neutral / Weakening / Headwind
- **Transition**: Strengthening / Stable / Weakening / Reversing

## 핵심 충돌 패턴

| 패턴 | 의미 |
|---|---|
| RS↑ + Catalyst↑ | Healthy Leadership |
| RS↑ + Catalyst↓ | Late Stage Leadership |
| Catalyst↑ + RS↓ | 잠재적 리더(시장 미인지) |
| Catalyst↑ + Participation↓ | 시장 미인지 / Speculative Move |
| Breadth↓ + Catalyst↑ | 초기 리더십 |

## 데이터 소스 (타 모듈과 가장 이질적)

News, Earnings Call Transcript, SEC Filing, Analyst Report, Commodity Price(FRED), Government Policy, Industry Report, CAPEX 발표 — **대부분 정성적·텍스트 기반**이며 나머지 5개 모듈(가격·거래량 시계열)과 데이터 성격이 본질적으로 다르다.

## Output Schema

```json
{"state":"Structural Tailwind","transition":"Strengthening","strength":4,"confidence":0.91,
 "narrative":"AI 투자 확대와 데이터센터 CAPEX 증가가 섹터를 지지하고 있다.",
 "risks":["CAPEX 둔화","정책 변화"]}
```

## Limitations

정량화가 어렵고, 시장의 기대가 이미 선반영되어 있을 수 있다. 강한 Catalyst가 강한 수익률을 보장하지 않는다.

## ✅ 데이터 소싱 — 해결

뉴스는 Finnhub/NewsAPI 무료티어로, SEC 공시는 EDGAR Full-Text Search(키리스)로 충당한다. 실적콜 "전체 트랜스크립트" NLP는 유료 의존도가 높아 **범위를 축소** — 8-K 실적보도자료의 정형 가이던스 수치만 사용하는 것으로 별도 NLP 파이프라인 없이 처리한다. 상세는 `../data_sourcing.md` "§26/§37 Catalyst" 참조(`90_open_questions.md` C-10 해결).
