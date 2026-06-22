# 고도 분리 — 증시 / 섹터 / 개별주 모니터링 항목 분류 (선행 작업)

> **이 문서의 범위**: `00_architecture.md`의 4단 캐스케이드를 짓기 전에 **반드시 먼저 끝내야 하는 선행 작업** — 현재 "매크로 대시보드"(`backend/api/contract.md`의 `MarketPayload`)에 섞여 있는 항목들을 **증시(Market) / 섹터(Sector) / 개별주(Stock)** 세 고도로 명확히 갈라, 각 항목이 어느 tier로 가야 하는지 확정한다. 이 분류가 `00_architecture.md` §5(Macro 리트로핏 매핑)·§11(마이그레이션)의 **입력**이 된다.
>
> **계기**: 사용자 관찰(2026-06-22) — "EPS 같은 개별주 관련 항목이 매크로 대시보드에 섞여 있는 것 같다. 증시 모니터링과 개별주 모니터링을 명확히 구분하는 작업이 먼저 선행돼야 한다."

---

## 0. 사용자 관찰의 정교화

관찰은 정확하다. 다만 코드로 확정하면 그림이 한 단계 더 구체적이다:

1. **EPS/PER은 사실 "지수 집계" = 증시 항목이다.** `config.json`의 `KOSPI_forward_eps`/`NASDAQ_forward_eps`는 지수 전체의 합산 선행 EPS이고, `scoring.py:ceiling_levels()`는 `지수천장 = forward_eps × 멀티플`(KOSPI 9~15x · NASDAQ 23~38x)로 쓴다. 따라서 `flow.fwdPER`·`flow.trailingPER`·`bands`·`reconciliation.supportedCeiling`은 **개별주가 아니라 지수 밸류에이션**이다. 이름이 EPS라 개별주처럼 보일 뿐.
2. **진짜 개별주 항목은 `leaders` 블록이다.** `sectors.json`의 key/star 종목(삼성전자·SK하이닉스 등)이 role·thesis·stats·risk·price·ytd까지 담아 macro payload(`leaders`)에 박혀 있고, 프론트 `LeadershipSection`(LAYER 3)이 종목 카드로 렌더한다.
3. **현재 대시보드는 2고도가 아니라 3고도가 섞여 있다.** 증시 + 섹터(`sectors[]`/RRG/트리맵) + 개별주(`leaders`). 특히 **LAYER 3 "주도 (섹터·종목)"가 섹터와 종목을 한 섹션에 합쳐놓은 것**이 구조적 핵심 문제다.

---

## 1. 핵심 결론

- **증시(Market)** 항목 → Macro tier 유지 (EPS/PER/bands 포함 — 단, "지수 집계"임을 네이밍으로 명시).
- **섹터(Sector)** 항목(`sectors[]`, RRG, 트리맵) → Sector tier로 이관.
- **개별주(Stock)** 항목(`leaders` 블록 전체) → Stock tier로 이관.
- 정제 후 **Macro payload는 "증시 전용"** 이 된다 — 섹터·종목 데이터를 담지 않는다.

---

## 2. 고도 정의 + 식별 기준

| 고도 | 분석 단위(entity) | 한 줄 정의 | 식별 기준 (이게 헷갈리면 이걸로 가른다) |
|---|---|---|---|
| **증시 Market** | market 1개 (KOSPI/NASDAQ) | "시장 전체가 위험 선호 환경인가?" | **집계 단위가 지수 전체**이면 증시. 지수레벨·지수 집계 밸류에이션·유동성·심리·시장 폭. |
| **섹터 Sector** | sector_code N개 | "어느 섹터로 자금이 이동하는가?" | 집계 단위가 **섹터**이면 섹터. RRG·섹터 YTD·섹터 시총·quadrant. |
| **개별주 Stock** | ticker 1개 | "어떤 종목을 선택하는가?" | 집계 단위가 **종목 1개**이면 개별주. 종목 가격/EPS/PER/thesis/risk. |

> **단일 판별 규칙**: *"이 숫자는 무엇을 1단위로 집계한 것인가?"* — 지수 전체 → 증시 / 섹터 → 섹터 / 종목 하나 → 개별주. 지표 이름(EPS, PER, RS, breadth)이 아니라 **집계 단위**가 고도를 결정한다.

---

## 3. 현재 `MarketPayload` 전수 분류

| 현재 payload 필드 | 고도 | 목적지 tier | 비고 |
|---|---|---|---|
| `flow.level`, `chgPct`, `yoyPct`, `spark` | 증시 | Macro | 지수 가격/추세 |
| `flow.breadthText`, `breadthNote` | 증시 | Macro | 시장 폭(상승/하락 종목수 또는 섹터 등락수) — 시장 전체 집계 |
| `flow.volValue`, `volLabel`, `volDir` | 증시 | Macro | VIX/VKOSPI(실현변동성) |
| **`flow.fwdPER`, `flow.trailingPER`** | 증시 | Macro | ⚠️ **지수 집계 밸류에이션** — 개별주 아님. §4 네이밍 규칙 적용 |
| **`bands` (base/bull/hyper)** | 증시 | Macro | 지수 천장 = 지수 집계 EPS × 멀티플 |
| `regime` (composite, label) | 증시 | Macro | 유동성 레짐 |
| `fearGreed` (score, factors) | 증시 | Macro | 시장 심리 |
| `reconciliation` (state, supportedCeiling, priceBand, distancePct) | 증시 | Macro | 지수 가격밴드 vs 레짐 정합성 |
| `sources` (S01~S06) | 증시 | Macro | 유동성 동인 6축(중앙은행·외국인·신용·대기자금·환율·글로벌신용) |
| `watchlist` | 증시 | Macro | 매크로 트리거(Fed·외국인·신용·MMF·USDKRW·OAS/VIX·breadth) |
| `narrative.flow`, `liquidity`, `reconciliation` | 증시 | Macro | 증시 서술 |
| **`sectors[]`** (marketCap, ytd, rsRatio, rsMomentum, quadrant) | **섹터** | **Sector** | RRG/순환매/트리맵 — Sector Engine §21/§24로 이관 |
| `narrative.leadership` (섹터 부분) | 섹터 | Sector | 섹터 Rulebook narrative로 이동 |
| **`leaders{}`** (key/star: ticker, name, role, price, ytd, thesis, stats, risk, asOf) | **개별주** | **Stock** | ★ 진짜 개별주 content — Stock Engine으로 이관 |
| `narrative.leadership` (종목 부분) | 개별주 | Stock | 종목 Rulebook narrative로 이동 |
| `market`, `asOf`, `source`, `pill`, `freshness`, `_mode` | meta | (각 tier 공통 envelope) | 유지 |

---

## 4. EPS/PER 모호성 해소 — "집계 단위" 규칙

사용자가 EPS를 짚은 건 **표면적으론 오인이지만 구조적으론 정확한 경고**다:

- **현재**: `fwdPER`/`trailingPER`/`bands`는 지수 집계 → 증시에 **올바르게** 속한다. 이관하지 않는다.
- **다가오는 충돌**: Stock Engine §32 Expectation이 들어오면 **같은 종류의 지표(EPS·PER·컨센서스·revision)가 "종목 단위"로 다시 등장**한다. 지금 이름을 그냥 `forward_eps`로 두면 §32의 종목 EPS와 코드·UI·DB에서 충돌·혼동된다.
- **선제 결정 (네이밍으로 고도 못박기)**:

| 지표 | 증시(Macro) 네이밍 | 개별주(Stock §32) 네이밍 |
|---|---|---|
| 선행 EPS | `index_forward_eps` (config: `KOSPI_index_forward_eps`) | `stock.expectation.forward_eps[ticker]` |
| 선행 PER | `index_fwd_per` | `stock.expectation.fwd_per[ticker]` |
| 밸류에이션 밴드 | `index_valuation_bands` | (해당 없음 — 종목은 멀티플 천장 모델 미적용) |

→ 데이터 평면 `series_id`·`config.json` 키·프론트 라벨 전부 `index_*` 접두로 고도를 표면화한다. 이게 "EPS가 개별주처럼 보인다"는 혼동을 영구히 제거한다.

> 🔶 **결정 필요**: 기존 `config.json` 키(`KOSPI_forward_eps`)를 `KOSPI_index_forward_eps`로 리네이밍할지(마이그레이션 1회) vs 현 키 유지하고 문서/라벨만 명시할지. 권장: **리네이밍** — §32 도입 전이 비용이 가장 싸다.

---

## 5. 핵심 구조 문제 — LAYER 3가 섹터+종목 혼재

프론트가 고도 혼재를 그대로 드러낸다:

| 현재 프론트 섹션 | 렌더 내용 | 고도 | 분리 후 |
|---|---|---|---|
| LAYER 1 "흐름" (`FlowSection`) | 지수가·breadth·변동성·**선행 PER** | 증시 | MacroView 유지 (PER 라벨 "지수 선행 PER"로 명시) |
| `LiquiditySection` | bands·regime·fearGreed·reconciliation·sources | 증시 | MacroView 유지 |
| **LAYER 3 "주도 (섹터·종목)" (`LeadershipSection`)** | 트리맵·RRG(**섹터**) + 주도주 카드(**개별주**) | **섹터+개별주 혼재** | **분할**: 섹터 → SectorView, 종목 카드 → StockView |
| `WatchlistTable` | 매크로 트리거 | 증시 | MacroView 유지 |

→ `LeadershipSection` 분할이 이 선행 작업의 **프론트 측 핵심 액션**이다. 섹션 제목이 문자 그대로 "섹터·종목"인 게 혼재의 증거.

---

## 6. 이 분류가 강제하는 선행 액션

`00_architecture.md` 마이그레이션(§11)에 앞서, 또는 그 1·2단계와 함께 수행:

1. **`leaders` 블록 추출** — macro payload에서 제거, Stock tier 입력으로 이전. `sectors.json`의 key/star/leaders/thesis는 Stock Engine 콘텐츠로 소유권 이전(파일은 유지하되 의미 재배치).
2. **`sectors[]` 추출** — macro payload에서 제거, Sector tier로. macro는 RRG 단일윈도우 스냅샷(크로스 내러티브 배지)만 소비(`00_architecture.md` §6.4 single source).
3. **Macro payload 정제** — 증시 전용으로. `narrative`에서 leadership 항목 제거(섹터/종목 Rulebook으로 이동).
4. **EPS/PER 네이밍 `index_*` 적용** (§4) — §32 도입 전 선제.
5. **`LeadershipSection` 분할** (§5) — 섹터 UI ↔ 종목 UI 분리.

> **무중단 유지**: 위는 `00_architecture.md` §7.3의 `_adapter_legacy.py`가 당분간 기존 동결 payload를 계속 생성하는 동안 새 tier별 엔드포인트로 점진 이전하는 방식으로 진행. 동결 payload는 회귀 oracle로 마지막까지 유지.

---

## 7. 참조

| 문서 | 연결점 |
|---|---|
| `00_architecture.md` §5 | Macro 리트로핏 매핑 — 본 분류가 그 입력 |
| `00_architecture.md` §6.4 | RRG single source — `sectors[]` 이관과 연결 |
| `00_architecture.md` §11 | 마이그레이션 단계 — 본 선행 액션이 1·2단계 전제 |
| `blueprint_micro/stock_engine/32_expectation.md` | §32 종목 EPS/PER — §4 네이밍 충돌의 상대 |
| `backend/api/contract.md` | 현 `MarketPayload` — 분류 대상 원본 |
