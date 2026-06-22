# Micro Intelligence Layer — Blueprint 지도

> **이 폴더가 다루는 범위**: `planning/micro Ideation/` 안의 16개 원본 스펙(PDF)을 읽고 압축한 결과물이다. 매크로 분석(기존 `기획안_v3.md` / `blueprint_v3.md`)에 **다음으로 붙는 레이어** — Sector Intelligence Engine(§20~29)과 Stock Intelligence Engine(§30~39)을 다룬다. 원본을 통째로 옮기지 않고, 각 모듈의 핵심(질문·철학·State/Transition·충돌패턴·Output Schema·한계)만 추출했다. 전체 계산식·전체 State 목록 등 세부사항이 필요하면 각 파일 상단에 적힌 원본 PDF를 직접 참조할 것.

## 0. 큰 그림 — 4단 엔진 구조

```
Macro Engine        (기존, 기획안_v3.md / blueprint_v3.md)
   ↓  "시장 전체가 위험 선호 환경인가?"
Sector Engine        (신규, 본 폴더 sector_engine/) — §20~29
   ↓  "어느 섹터로 자금이 이동하는가?"
Stock Engine         (신규, 본 폴더 stock_engine/) — §30~39
   ↓  "어떤 종목을 선택해야 하는가?"
Strategy Engine      (미설계 — 원본 어디에도 내용 없음, 다이어그램상 이름만 존재)
   ↓  "얼마를 언제 어떻게 넣을 것인가?"
```

핵심 철학은 4단 전체에서 동일하다: **모듈 점수를 합산하지 않는다. 불일치(Conflict)가 가장 중요한 정보다.** 기존 매크로 엔진의 "6축 합산 금지" 원칙(`blueprint_v3.md` §4)이 Sector/Stock Engine에도 그대로 계승되어 있다.

## 1. 폴더 구조

```
blueprint_micro/
├── 00_index.md              ← 이 파일
├── 90_open_questions.md     ← Opus 검토용 이슈 전체 집계
├── data_sourcing.md         ← 데이터 소싱 분류(키리스/무료키/유료) — 2026-06-21 추가
├── sector_engine/
│   ├── 00_overview.md            (§20)
│   ├── 21_relative_strength.md   22_breadth.md   23_participation.md
│   ├── 24_rotation.md   25_momentum.md   26_catalyst.md
│   └── 29_rulebook.md            (해석 레이어)
└── stock_engine/
    ├── 00_overview.md            (§30)
    ├── 31_quality.md   32_expectation.md   33_positioning.md
    ├── 34_price_structure.md   35_relative_strength.md   36_participation.md
    ├── 37_catalyst.md 🆕Claude작성   38_risk.md
    └── 39_rulebook.md 🆕Claude작성
```

## 2. Sector Intelligence Engine 한눈에 보기 (§20~29)

| § | 모듈 | 한줄 질문 |
|---|---|---|
| 21 | Relative Strength | 어느 섹터가 시장보다 강한가? |
| 22 | Breadth | 상승이 건강하게 확산되는가? |
| 23 | Participation | 실제 자금이 들어오는가? |
| 24 | Rotation | 자금은 공격형↔방어형 중 어디로? |
| 25 | Momentum | 강해지고 있는가? |
| 26 | Catalyst | 왜 움직이는가? |
| 29 | Rulebook | 위 6축 종합 → Direction/Strength/Conviction |

상세는 `sector_engine/00_overview.md`부터 읽을 것.

## 3. Stock Intelligence Engine 한눈에 보기 (§30~39)

| 계층 | § | 모듈 | 한줄 질문 |
|---|---|---|---|
| Fundamental | 31 | Quality | 좋은 회사인가? |
| Fundamental | 37 | Catalyst 🆕 | 왜 움직이는가? |
| Fundamental | 38 | Risk | 무엇이 틀릴 수 있는가? |
| Market | 32 | Expectation | 시장은 무엇을 기대하는가? |
| Market | 33 | Positioning | 누가 들고 있는가? |
| Price | 34 | Price Structure | 언제 살 것인가? |
| Price | 35 | Relative Strength | 시장이 뭘 사고 있는가? |
| Price | 36 | Participation | 돈이 들어오는가? |
| — | 39 | Rulebook 🆕 | 8축 종합 |

🆕 = 원본 PDF 없음, Claude가 사용자 승인 하에 새로 설계(2026-06-21). 파일 상단에 동일 표시가 있다.

상세는 `stock_engine/00_overview.md`부터 읽을 것.

## 4. 기존 매크로 엔진(blueprint_v3/기획안_v3)과의 핵심 접점 — 결정 완료 (2026-06-21)

신규 레이어를 매크로 엔진에 "붙이기" 위해 필요했던 3가지 결정이 사용자 지시에 따라 모두 내려졌다(상세는 `90_open_questions.md` B번):

1. **RRG/로테이션 중복 → 모듈화로 해결**: 기존 v2 "주도(RRG)"(`기획안.md` §5-2) + §13-3 "섹터 공·수 로테이션"의 원시 계산을 **단일 출처**로 채택하고, 신규 §21/§24는 그 위에 다중 시간축·세부 분류만 추가하는 구조로 분리했다. 같은 공식을 두 곳에서 따로 구현하지 않는다. → `sector_engine/21_relative_strength.md`·`24_rotation.md`의 "Macro Engine과의 데이터 계약" 절.
2. **검증 게이트 → 유보 결정**: 매크로 v3의 base-rate 보정 + 0.6 상한 + walk-forward 게이트(`기획안_v3.md` §4)를 신규 레이어에 지금 강제하지 않는다. 충분한 트레이드/결과 데이터가 누적된 뒤 별도 단계로 추진하기로 결정 — 그 전까지 모든 confidence·conviction 값은 "비검증 휴리스틱(랭킹 신호)"로 취급한다. → `stock_engine/39_rulebook.md` §8(정책 전문), `sector_engine/29_rulebook.md`.
3. **데이터 레이어 확장 → 무료/무료키 우선 원칙으로 재정리**: 13F·공매도·다크풀·내부자매매·애널리스트 컨센서스는 대부분 SEC EDGAR/FINRA(키리스)·Finnhub/FMP(무료키)로 충당 가능하도록 재매핑했다. 유일하게 무료 대체가 어려운 실적콜 전체 트랜스크립트는 범위를 축소(정형 가이던스 수치만 사용)해 제거했다. → `data_sourcing.md`.

## 5. 주요 설계 결정 요약 (2026-06-21)

- **§37 Stock Catalyst** — Claude가 §26 Sector Catalyst 상속 구조를 기반으로 새로 설계(원본 PDF 없음, 파일 상단에 명시).
- **§39 Stock Rulebook** — Claude가 §29 Sector Rulebook 형식을 3계층 구조에 맞게 새로 설계(원본 PDF 없음, 파일 상단에 명시). 가중치 축과 거부권 축을 분리하고, Sector→Stock 인터페이스와 `position_size_hint` 출력을 명문화했다.
- **Sector §21/§24 ↔ 매크로 엔진** — 데이터 계약으로 중복 해소(위 §4-1).
- **데이터 소싱** — `data_sourcing.md`로 전면 재정리.

### 잔존 미결 사항 (이번 라운드에서 다루지 않음)

- **Strategy Engine** — 다이어그램상 이름만 존재, 내용 전무. 이번 결정에서 범위 밖.
- Horizon(T0~T3) 명명이 기존 매크로 §15(T1/T2)와 불일치 — 미해결.
- State 경계 정량 기준, confidence/strength 산식 — 전 모듈 공통 후속 "정량화 패스" 필요(미해결).
- 섹터 엔진 §27·§28 번호 결번 — 사소, 미해결.
- 상세는 `90_open_questions.md` 참조(해결 항목은 ✅로 갱신됨).

## 6. 읽는 순서 제안

1. 본 파일 → 2. `sector_engine/00_overview.md` → 3. sector_engine 모듈 6개(21~26) → 4. `sector_engine/29_rulebook.md` → 5. `stock_engine/00_overview.md` → 6. stock_engine 모듈(31~38, §37 포함) → 7. `stock_engine/39_rulebook.md` → 8. `data_sourcing.md` → 9. `90_open_questions.md`로 전체 이슈 재확인.
