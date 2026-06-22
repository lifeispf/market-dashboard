# 통합 아키텍처 — Unified Engine Blueprint

> **이 문서가 다루는 범위**: 현재 따로 자라난 두 줄기 — **구현 완료된 Macro 분석**(`macro Ideation/blueprint_v3.md`, `backend/`, `frontend/`)과 **기획만 완료된 Micro 분석**(`blueprint_micro/`, 코드 0) — 을 *하나의 통일성 있는 앱 플로우*로 합치기 위한 **아키텍처 결정 문서**다. 개별 모듈의 계산식·State 목록은 다루지 않는다(그건 `blueprint_micro/`와 `macro Ideation/`이 이미 가지고 있다). 이 문서는 **그 둘을 같은 추상화 위에 올리고 4단 캐스케이드로 연결하는 뼈대**만 정의한다.
>
> **상위 맥락**: `blueprint_micro/00_index.md` §0의 "4단 엔진 구조"(Macro→Sector→Stock→Strategy)를 실제 코드 아키텍처로 번역한 것이다.
> **작성**: 2026-06-22. 선행 결정들(2026-06-21, `blueprint_micro/90_open_questions.md`)을 전제로 한다.

---

## 0. 왜 이 문서가 필요한가 — 현재 상태 진단

| 구분 | Macro 분석 | Micro 분석 (Sector/Stock) |
|---|---|---|
| 성숙도 | **구현 완료** (FastAPI + React + SQLite) | **기획만 완료** (`blueprint_micro/`, 코드 0) |
| 코드 구조 | `backend/api/market.py:assemble_payload()` — **단일 ~550줄 함수**가 fetch·scoring·RRG·leaders·narrative·freshness를 절차적으로 전부 처리 | 설계상 **모듈/Rulebook 패턴** — 각 모듈은 독립 observer, Rulebook이 종합 |
| 모듈 추상화 | 코드 레벨 없음 (개념상 S01~S06은 `scoring.py`의 함수들) | 명시적 (`Question→Indicators→State→Transition→Conflict`) |
| 출력 형태 | 동결된 평면 `MarketPayload` 1종 (`backend/api/contract.md`) | `{state, transition, strength, confidence, narrative}` → Rulebook → `{direction, strength, conviction, ...}` |
| 철학 | "6축 합산 금지, 불일치=신호" (개념은 있으나 코드엔 안 녹음) | **동일 철학을 명시적으로 계승** |

### 핵심 모순

두 모듈은 **같은 철학**을 공유하는데 표현 방식이 다르다 — macro는 모놀리식 절차 코드, micro는 모듈 추상화 설계. 이대로 micro를 구현하면 "서로 다른 부품으로 만든 두 기계"가 되어 통일성이 깨진다.

→ **"통일성 있는 앱 플로우"의 진짜 정의**: UI를 합치는 게 아니라, **두 엔진을 같은 추상화 위에 올리고(§2~4), 4단 캐스케이드로 연결하며(§4.3), 같은 출력 envelope을 API·프론트가 그대로 흘려보내게(§7~8)** 만드는 것이다.

---

## 1. 설계 원칙

### 1.1 계승 (기존 macro 엔진에서)

1. **6축 합산 금지** — 평균 내면 불일치 정보가 사라진다. (`blueprint_v3.md` §4-1)
2. **불일치(Conflict)가 가장 중요한 신호** — 충돌 카탈로그로 형식화. (§15 X1~X7, §29/§39 패턴 A~J)
3. **Graceful degradation** — 데이터 미가용은 항상 null/unknown, 절대 크래시·임의값 금지. (`contract.md` 불변식)
4. **판단값/콘텐츠/데이터 3계층 분리** — `config.json`(판단값) · `sectors.json`(콘텐츠) · DB(시계열·계산값). (`데이터저장구조.md` §1)

### 1.2 신규 (통합을 위해)

5. **단일 추상화** — micro의 Module/Rulebook 계약을 **4단 전체의 공용 규약**으로 승격, macro를 거기에 리트로핏. (§2)
6. **타입드 캐스케이드** — 상위 tier verdict가 하위 tier의 context(=필터)가 된다. (§4.3, §39 §5의 Sector→Stock 인터페이스를 일반화)
7. **공유 데이터 평면** — 같은 데이터를 엔진마다 따로 fetch하지 않는다. RRG 같은 공유 계산은 single source of truth. (`data_sourcing.md` "공유 원칙", `blueprint_micro/00_index.md` §4-1)
8. **검증 게이트를 1급 시민으로** — confidence/conviction은 walk-forward 통과 전까지 "비검증 휴리스틱". `verified` 플래그를 출력 envelope에 처음부터 박는다. (§9.1, `39_rulebook.md` §8)

---

## 2. 핵심 통찰 — micro 추상화를 공용 규약으로 승격

micro 블루프린트가 이미 정답을 들고 있다. **모든 분석 단위가 동일한 계약을 따른다:**

```
Observer Module  ──▶  (독립 관측, 합산 안 함)  ──▶  Rulebook  ──▶  Verdict
{state, transition,                              (해석만,         {direction, strength,
 strength, confidence,                            패턴 매칭)       conviction, narrative,
 narrative}                                                       risks, invalidation}
```

이걸 **micro 전용이 아니라 4단 공용 규약으로 채택**하고, 기존 macro의 S01~S06 / RRG / 공포탐욕을 이 계약에 맞춰 리트로핏하면 macro와 micro가 자동으로 "같은 부품으로 만든 같은 종류의 기계"가 된다.

> **통일성은 UI 통합이 아니라 이 추상화 통일에서 나온다.** 이것이 본 아키텍처의 단일 핵심 결정이다.

---

## 3. 5계층 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ⑤ PRESENTATION   단일 SPA · 드릴다운 플로우                                 │
│    Macro view ──click sector──▶ Sector view ──click stock──▶ Stock view    │
│    공용 프리미티브: <VerdictCard> <ModuleCard> <ConflictBadge> <ContextRail>│
├─────────────────────────────────────────────────────────────────────────┤
│ ④ API            tier별 리소스 + 공용 envelope                             │
│    /api/macro · /api/sectors · /api/stocks · /api/briefing(캐스케이드)      │
├─────────────────────────────────────────────────────────────────────────┤
│ ③ ENGINE CASCADE  타입드 파이프라인 (상위가 하위를 "필터")                  │
│    MacroEngine ─ctx─▶ SectorEngine ─ctx─▶ StockEngine ─ctx─▶ StrategyEngine│
│    └ 각 Engine = [독립 Module들] + Rulebook(해석)                           │
├─────────────────────────────────────────────────────────────────────────┤
│ ② ENGINE CORE     공용 프레임워크 (tier 무관) ★통일성의 본체★               │
│    Module · Engine · Rulebook · Verdict · ModuleOutput · Context · Horizon  │
├─────────────────────────────────────────────────────────────────────────┤
│ ① DATA PLANE      엔진 공유 단일 데이터 평면                                │
│    Providers(fred·yf·cboe·SEC·FINRA·Finnhub·DART)                          │
│    → Registry(series_map) → Ingest(증분) → Store(SQLite, series_daily)      │
│    ※ RRG 등 공유 계산은 single source of truth (매크로↔섹터 중복 금지)      │
└─────────────────────────────────────────────────────────────────────────┘
```

**핵심 규칙**: ②번 계층이 통일성의 본체다. ③④⑤는 모두 ②의 `Verdict`/`ModuleOutput` envelope을 그대로 흘려보내기만 한다 → 한 번 만든 프론트 컴포넌트·API 핸들러가 4단 전부에 재사용된다.

---

## 4. Engine Core — 통일 계약 (가장 중요)

모든 tier가 공유하는 타입. macro·sector·stock·strategy가 **전부 이 모양**으로 입출력한다.

### 4.1 공용 타입

```python
# engine/core/contracts.py
Horizon    = Literal["T0", "T1", "T2", "T3"]   # 전 tier 단일 정규 enum (§9.2 — macro T1/T2 ↔ micro T0~T3 불일치 해소)
Transition = Literal["improving", "stable", "weakening", "breaking"]
Direction  = Literal["strong_up", "up", "neutral", "down", "strong_down"]

@dataclass
class ModuleOutput:         # 독립 관측기 1개의 산출 — 결론을 내리지 않는다
    module_id: str          # "macro.S01" | "sector.relative_strength" | "stock.quality"
    state: str | None       # tier별 어휘(Leading.. | base/bull/hyper..); None = unknown(우아한 degrade)
    transition: Transition | None
    strength: float | None  # 0..1 정규화 (macro의 0~100 점수는 /100)
    confidence: float | None  # 비검증 휴리스틱 (§9.1)
    narrative: str
    inputs: dict            # 드릴다운/freshness용 원시값 보존

@dataclass
class Verdict:              # Rulebook 산출 — 모든 tier가 동일한 모양
    direction: Direction
    strength: int           # 0..4
    conviction: float | None
    lead_pattern: str | None       # "Strong Leader" | "Value Trap" | "Early Rotation" ...
    narrative: str
    risks: list[str]
    invalidation: list[str]
    horizon: Horizon
    verified: bool          # ★ expose_only_if_backtested 게이트 (§9.1)
    extra: dict             # tier별 확장(stock: position_size_hint / macro: supportedCeiling, reconciliation)

@dataclass
class EngineOutput:         # 한 tier 실행의 전체 결과 = API envelope의 원형
    tier: str               # "macro" | "sector" | "stock" | "strategy"
    entity_id: str          # macro→market, sector→code, stock→ticker
    verdict: Verdict
    modules: list[ModuleOutput]
    context: dict           # 나를 필터한 상위 tier verdict들
    freshness: list[dict]   # 기존 freshness 계승
    mode: Literal["live", "mock", "degraded"]
```

### 4.2 프로토콜 3종

```python
class Module(Protocol):                 # 독립 observer — 한 가지 질문만 본다
    id: str
    tier: str
    def available_for(self, market: str) -> bool: ...            # §9.4 — 한국 미지원 모듈은 False로 정직하게 빠짐
    def required_series(self, entity_id, ctx) -> list[str]: ...   # 데이터 평면 prefetch용
    def compute(self, entity_id, ctx, data) -> ModuleOutput: ...

class Rulebook(Protocol):               # 해석기 — fetch·합산 절대 안 함, 패턴 매칭만
    def interpret(self, modules: list[ModuleOutput], upstream: Context) -> Verdict: ...

class Engine:                           # tier 1개 = 모듈 N개 + Rulebook 1개
    tier: str
    modules: list[Module]
    rulebook: Rulebook
    def run(self, entity_id, ctx, data) -> EngineOutput:
        outs = [m.compute(entity_id, ctx, data)               # 독립 관측
                for m in self.modules if m.available_for(ctx.market)]
        verdict = self.rulebook.interpret(outs, ctx)           # 절대 평균 내지 않음 — 패턴/거부권만
        return EngineOutput(self.tier, entity_id, verdict, outs, ctx.as_dict(), ...)
```

**불변식**: Module은 fetch만 하고 결론을 내리지 않는다. Rulebook은 결론을 내리되 fetch도 합산도 하지 않는다. 이 분리가 "6축 합산 금지" 원칙을 **코드 레벨에서 강제**한다.

### 4.3 캐스케이드 — 통일 앱 플로우의 코드 표현

상위 verdict가 하위의 context(필터)가 된다. `39_rulebook.md` §5의 Sector→Stock 인터페이스를 일반 규칙으로 승격.

```python
# engine/cascade.py
def run_cascade(market, data) -> Cascade:
    macro   = macro_engine.run(market, Context.root(market), data)
    sectors = [sector_engine.run(c, Context.from_macro(macro), data)
               for c in sector_codes(market)]
    leading = pick_leading(sectors)                      # Rulebook direction/conviction으로 랭킹
    # §39 §5: Sector Strong Down/Breakdown → 종목 conviction 강제 하향; Strong Up → 상향 보너스
    stocks  = [stock_engine.run(t, Context.from_sector(leading), data)
               for t in tickers(leading)]
    return Cascade(macro=macro, sectors=sectors, stocks=stocks)
```

이 한 함수가 "Macro → Sector → Stock"을 한 줄기로 꿰는 통일 플로우의 본체다. 동시에 각 엔진은 **독립 실행도 가능**(상위 ctx를 neutral로 주면 됨) — 디버깅·부분 갱신·tier별 캐싱에 필수.

### 4.4 tier별 어휘 매핑

같은 `state`/`direction` 필드지만 tier별로 어휘가 다르다(계약은 통일, 값은 도메인별).

| tier | entity | state 어휘(예) | Rulebook | extra 필드 |
|---|---|---|---|---|
| macro | KOSPI/NASDAQ | base/bull/hyper(regime) | §15 방향·강도 루브릭 | supportedCeiling, reconciliation, fearGreed |
| sector | 섹터코드 | Leading/Improving/Weakening/Lagging | `29_rulebook.md` (패턴 A~J, Veto V1~V4) | rrgTail, quadrant |
| stock | 티커 | (모듈별) | `39_rulebook.md` (패턴 A~J, 거부권 축) | position_size_hint, layer별 종합 |
| strategy | 포지션 | (미설계) | 미설계 | sizing, hedge |

---

## 5. Macro 리트로핏 — 기존 코드 → 새 계약 매핑

> **선행 작업**: 이 매핑에 들어가기 전에 `01_altitude_separation.md`(증시/섹터/개별주 고도 분류)가 먼저 확정돼야 한다 — 현 macro payload에 섞인 `sectors[]`(→Sector)·`leaders`(→Stock)를 먼저 갈라내야 아래 "Macro 전용" 매핑이 성립한다.

기존 동작을 바꾸지 않고 단지 **재배치**한다. `assemble_payload()`를 해체해 아래로 흩뿌린다.

| 기존 (`market.py` / `scoring.py`) | 새 위치 | 비고 |
|---|---|---|
| `score_s01..s06()` | `engine/macro/modules/` 6개 `Module` | strength = score/100, transition = `trend_direction`, state = headroom 밴드 |
| `fear_greed` (`scoring_ext.py`) | `engine/macro/modules/fear_greed.py` | 독립 모듈 1개 |
| `composite_score` + `regime_from_score` + `reconciliation_status` | `engine/macro/rulebook.py` | direction ≈ regime, 정합성 = conflict 패턴, 합산 제거 |
| RRG / `rrg_quadrant` / sector 루프 | **Sector Engine §21/§24로 이관** | macro는 단일윈도우 스냅샷만 소비 → 중복 제거(§6 single source) |
| leaders 빌드 | Stock Engine 입력으로 흡수 | key/star 테제는 `sectors.json` 유지 |
| watchlist | macro Rulebook의 invalidation/risks로 흡수 | |
| 동결 `MarketPayload` | `EngineOutput → backend/api/_adapter_legacy.py` | **기존 프론트 무중단**(§7.3) |

> **회귀 검증 oracle**: `contract.md`의 불변식과 현 `_mode:"live"` payload가 그대로 회귀 테스트 기준이 된다. 리트로핏 후 어댑터 출력이 **바이트 동일**한지 확인 → 행동 무변화 보장.

---

## 6. 데이터 평면 (계층 ①)

`data_sourcing.md`의 "엔진 간 공유 단일 fetcher" 요구를 구조화. 기존 `backend/store/`가 이미 절반 완성 — `series_daily`는 임의 `series_id`를 수용하므로 micro로 그대로 확장된다.

### 6.1 Provider 인터페이스 통일

```python
class Provider(Protocol):
    name: str   # "fred" | "yfinance" | "cboe" | "sec_edgar" | "finra" | "finnhub" | "dart"
    def fetch(self, series_id: str, lookback_days: int) -> list[tuple[date, float]]: ...
```

기존 `data/fred_fetcher.py`·`leadership_fetcher.py`(yfinance)·`kr_fetcher.py`는 이 인터페이스로 래핑. 신규: cboe(풋콜)·SEC EDGAR(13F/8-K/Form4)·FINRA(공매도/다크풀)·Finnhub/FMP(컨센서스)·DART(한국).

### 6.2 provider 우선순위 — "공유되는 것부터"

| 순위 | provider | 무엇을 채우나 | 왜 먼저 |
|---|---|---|---|
| 1 | CBOE 풋콜 (키리스) | macro 공탐 F6 부활 **+** stock §32/§33 옵션 기대 | **macro·stock 동시 충족** (`data_sourcing.md` §32) |
| 2 | FINRA 공매도/다크풀 (키리스) | macro v3 Triage 포지셔닝 **+** stock §33 Positioning | **동일 소스 공유** (중복 호출 금지) |
| 3 | SEC EDGAR (키리스) | stock §32 가이던스·§33 13F/Form4·§37 8-K | 키리스, 파싱만 자체 구현 |
| 4 | Finnhub/FMP (무료키) | stock §32 컨센서스·revision | 무료키 1개 추가(config.json 등록) |
| 5 | DART (무료키) | 한국 종목 부분 보완 | §9.4 한계 인지 |

### 6.3 Store / Registry 확장

- **Registry(`series_map.py`)** — micro series 추가(per-stock 펀더멘털, 공매도, 13F, 옵션체인). 네이밍 규약 유지(`데이터저장구조.md` §8): 같은 데이터는 같은 논리 id 1개.
- **결과 저장 일반화** — 현 `scores_daily`(s01~s06 하드코딩)·`sector_metrics_daily`를 tier-무관 테이블로 확장:

```sql
-- 기존 scores_daily / sector_metrics_daily를 포섭하는 일반형 (추가, 기존은 마이그레이션)
CREATE TABLE IF NOT EXISTS engine_verdicts (
    tier        TEXT NOT NULL,   -- 'macro' | 'sector' | 'stock' | 'strategy'
    entity_id   TEXT NOT NULL,   -- market | sector_code | ticker
    date        TEXT NOT NULL,
    direction   TEXT, strength INTEGER, conviction REAL,
    lead_pattern TEXT, verified INTEGER,
    payload_json TEXT,           -- 전체 Verdict 직렬화(모듈 states 포함)
    PRIMARY KEY (tier, entity_id, date)
);
```

→ stock/strategy verdict도 누적 → 훗날 walk-forward 검증 게이트(§9.1)의 직접 입력이 된다. `series_daily`는 변경 없음.

### 6.4 단일 진실 원천 (Single Source of Truth)

RRG/로테이션은 **한 곳에서만 계산**(`engine/data/shared/rrg.py`), macro 배지와 sector 엔진이 동일 원시값을 재해석한다 — `blueprint_micro/00_index.md` §4-1 결정 그대로. "같은 공식을 두 곳에서 따로 구현하지 않는다."

---

## 7. API 계층 (계층 ④)

### 7.1 리소스 맵 — tier별, 전부 동일 envelope

```
GET /api/macro/{market}              ─ macro verdict + 6축
GET /api/sectors/{market}            ─ 섹터 랭킹 (macro ctx 소비)
GET /api/sectors/{market}/{code}     ─ 섹터 딥다이브 (6모듈 + rulebook + RRG tail)
GET /api/stocks/{market}/{code}      ─ 섹터 내 종목 랭킹 (sector ctx 소비)
GET /api/stocks/{market}/{ticker}    ─ 종목 딥다이브 (8모듈 + rulebook + position_size_hint)
GET /api/briefing/{market}           ─ 전체 캐스케이드 1회 (랜딩용)
GET /api/health                      ─ 기존 유지
```

### 7.2 공용 envelope

모든 응답이 `EngineOutput` 직렬화 = `{tier, entityId, verdict, modules, context, freshness, mode}`. 프론트는 tier를 몰라도 렌더 가능.

### 7.3 동결 payload 호환

`backend/api/market.py`의 `GET /api/market/{market}`는 **당분간 유지** — `_adapter_legacy.py`가 `MacroEngineOutput → 기존 MarketPayload`로 변환. 기존 프론트가 무중단으로 돌아가는 동안 새 `/api/macro`를 병행 구축, 프론트 마이그레이션 완료 후 제거.

---

## 8. 프론트엔드 (계층 ⑤)

### 8.1 단일 드릴다운 (별도 대시보드 2개가 아니라 1개)

```
MacroView (랜딩)  ──click sector──▶  SectorView  ──click stock──▶  StockView
   레짐/6축              섹터 rulebook + 6모듈 카드       종목 rulebook + 8모듈(3계층) + size hint
```

### 8.2 공용 프리미티브 3종 + ContextRail

envelope이 동일하므로 **모든 tier에 재사용**된다:

- `<VerdictCard>` — direction/strength/conviction/narrative/risks/invalidation (+ `verified` 라벨)
- `<ModuleCard>` — state/transition/strength/confidence/narrative
- `<ConflictBadge>` — lead_pattern + 충돌 표시
- `<ContextRail>` — **상시 표시**: `Macro 레짐 → Sector 방향 → Stock verdict`. 상위 맥락이 현재 화면을 어떻게 필터하는지 사용자가 늘 본다. ← **"통일 플로우"의 UX 본체**

### 8.3 기존 컴포넌트 처리

현 14개 macro 컴포넌트(`frontend/src/components/`)는 MacroView로 격하 흡수. RRGChart는 SectorView로 승격(tail 포함). types.ts는 envelope 1종으로 재작성.

---

## 9. 횡단 관심사 (1급 시민)

### 9.1 검증 게이트 (`verified`)

블루프린트가 반복 강조: conviction/confidence는 walk-forward 통과 전까지 **"비검증 휴리스틱"**(`39_rulebook.md` §8, `29_rulebook.md`). `Verdict.verified` 플래그를 envelope에 **처음부터** 박아, 프론트가 미검증 확률을 라벨/은닉(`expose_only_if_backtested`). 나중에 붙이면 4단 전체를 손봐야 한다.
> ✅ 결정(2026-06-21 계승): 검증 게이트 자체는 데이터 누적 후 별도 단계. 그 전까지 모든 confidence/conviction = "랭킹 신호"로만 취급, `verified=false`.

### 9.2 Horizon 통일

macro §15의 T1/T2(T1=1~5일, T2=1~4주)와 micro의 T0~T3(`30_stock_engine`)가 **같은 단어 다른 기간** — `blueprint_micro/00_index.md` §5 미해결 이슈. `Horizon` 단일 enum(`T0~T3`)으로 정규화하고, macro 모듈은 매핑 테이블로 흡수.
> 🔶 **결정 필요**: 정규 Horizon 경계값 확정. 잠정: T0=1~5거래일, T1=1~6주, T2=1~6개월, T3=1~2년(micro 기준 채택, macro를 매핑).

### 9.3 우아한 degrade

micro 데이터(SEC/FINRA 파싱)는 macro보다 훨씬 불안정. 계약에 명문화: `state=None` / `confidence=None` 허용, Engine은 `mode="degraded"` 표기, **절대 500 금지**(현 macro 불변식 계승·확장). Rulebook은 결손 모듈을 "관측 안 됨"으로 처리하되 가짜값으로 메우지 않는다.

### 9.4 한국 커버리지 갭

micro Market Layer(§32 Expectation·§33 Positioning)는 US 전용(13F/FINRA/SEC). `Module.available_for(market)`로 한국에선 정직하게 빠진다. Price Layer(§34~36)는 KODEX/TIGER로 한국 가능, Market Layer는 DART로 제한 보완. (`data_sourcing.md` "한국 시장 커버리지")

---

## 10. 제안 디렉토리 구조

```
engine/                              ← 신규: 엔진 코어 + 4 tier
├── core/        contracts.py · engine.py · rulebook.py · context.py · horizon.py
├── data/        providers/(fred,yf,cboe,sec,finra,finnhub,dart) · registry.py · ingest.py · store.py
│                shared/(rrg.py)     ← single source of truth
├── macro/       modules/(s01..s06, fear_greed) · rulebook.py · engine.py
├── sector/      modules/(relative_strength,breadth,participation,rotation,momentum,catalyst) · rulebook.py · engine.py
├── stock/       modules/(quality,expectation,positioning,price_structure,rs,participation,catalyst,risk) · rulebook.py · engine.py
├── strategy/    (스텁 — position_size_hint 소비자, 추후)
└── cascade.py
backend/
├── main.py                         ← 라우터만 추가
└── api/         macro.py · sectors.py · stocks.py · briefing.py · _envelope.py · _adapter_legacy.py · health.py
frontend/src/
├── primitives/  VerdictCard · ModuleCard · ConflictBadge · ContextRail
├── views/       MacroView · SectorView · StockView
├── components/  (기존 14개 — MacroView 내부로 정리)
└── api/         client.ts · types.ts (envelope 1종)
```

`config.json`/`sectors.json`/`scoring.py`는 유지(판단값·콘텐츠 분리 계승). `scoring.py`의 순수 계산 함수는 module들이 호출(재사용). 기존 `backend/store/`는 `engine/data/store.py`로 흡수·일반화.

---

## 11. 마이그레이션 단계 (무중단)

| 단계 | 내용 | 검증 | 상태(2026-06-22) |
|---|---|---|---|
| 1 | **Engine Core 골격** — 타입/프로토콜만(`engine/core/`) | 단위 테스트 | ✅ `642c53a` |
| 2 | **Macro 리트로핏(무행동변화)** — S01~S06 모듈 추출, `MacroEngine.run()` + `_adapter_legacy` | 동결 payload **바이트 동일** | ✅ `25fc45c` (KOSPI·NASDAQ 등가성 통과) |
| 3 | **데이터 평면 확장** — 키리스부터(CBOE 풋콜·FINRA) = macro v3 Triage 동시 충족 | synthetic→실데이터 | ⬜ 보류 (소비자=Stock §32/§33, 키/네트워크 필요 → Stage 5 심화 직전) |
| 4 | **Sector Engine** — 6모듈+rulebook, macro RRG를 §21/§24 단일원천 재사용 | 서버기동 | 🟡 §21 RS만(`e58b7ed`, `/api/sectors`). §22~26·§24는 데이터 평면 후 |
| 5 | **Stock Engine** — 8모듈+rulebook, Sector→Stock 인터페이스(§39 §5) 배선 | 서버기동 | 🟡 Price 레이어(§35 RS·§34 구조)만(`77e8e19`, `/api/stocks`). §31/§32/§33/§36은 데이터 평면 후 |
| 6 | **프론트 드릴다운** — 프리미티브 3종 + Sector/Stock view + ContextRail | preview 검증 | 🟡 `<VerdictCard>`·`<ModuleCard>` + SectorView(`63c4a98`)·StockView(`fccf909`) preview 검증 완료. ContextRail은 미구현 |
| 7 | **Strategy Engine** — 마지막(verdict 누적 데이터 필요) | — | ⬜ |
| + | **캐스케이드** — `run_cascade` + `/api/briefing` (Macro→Sector→Stock context 전파) | context 체인 테스트 | ✅ `caf84bd` |

> **진행 메모(2026-06-22)**: 3·4 순서 조정 — 3(데이터 평면)의 소비자는 5(Stock §32/§33)이고
> 키/네트워크가 없는 환경이라 실데이터 검증 불가 → 기존 DB 데이터로 검증 가능한 4·5(Price/RS
> 레이어)·6 프론트·캐스케이드를 먼저 구현. 남은 작업: ① 데이터 평면(3) — CBOE 풋콜/FINRA 공매도/
> SEC/Finnhub provider, ② 그 위에 Sector §22~26 / Stock §31·§32·§33·§36 모듈, ③ ContextRail
> 프론트(/api/briefing 소비), ④ Strategy Engine(7), ⑤ 고도 분리 마무리(leaders/sectors[]를
> 동결 payload에서 제거 — 프론트가 신규 tier 엔드포인트로 완전 이전한 뒤).

각 단계는 기존 워크플로(**synthetic 검증 → 실데이터 검증 → 서버기동 확인**) 그대로.

---

## 12. 미결 사항 / Opus 검토 대상

- **Strategy Engine** — 다이어그램상 이름만, 내용 전무. 본 아키텍처는 `position_size_hint`를 잠정 입력으로 두고 4번째 tier 슬롯만 예약. (`blueprint_micro/00_index.md` §5)
- **Horizon 경계값 확정** — §9.2. 잠정안 채택했으나 정식 결정 필요.
- **confidence/conviction 산식** — "몇 개 모듈 정렬 시 몇 점인가" 미정. 정책(비검증 취급)은 결정됐으나 공식은 구현 과제. (`90_open_questions.md` D-13)
- **`engine_verdicts` ↔ 기존 `scores_daily`/`sector_metrics_daily` 마이그레이션 경로** — 신규 테이블 병행 후 백필 vs 즉시 전환, 결정 필요.
- **OpenBB AGPL 라이선스** — 상업 임베딩 시 코드공개 의무. 데이터 평면이 obb.* 의존 시 영향. (`blueprint_v3.md` §5)

---

## 13. 참조 문서

| 문서 | 역할 |
|---|---|
| `01_altitude_separation.md` | **선행 작업** — 증시/섹터/개별주 고도 분류 (본 문서 §5·§11의 입력) |
| `blueprint_micro/00_index.md` | 4단 엔진 구조 원본 지도 (본 문서의 상위 맥락) |
| `macro Ideation/blueprint_v3.md` | Macro 엔진 모듈 지도 |
| `blueprint_micro/sector_engine/29_rulebook.md` | Sector Rulebook 출력 계약 |
| `blueprint_micro/stock_engine/39_rulebook.md` | Stock Rulebook + Sector→Stock 인터페이스(§5) |
| `blueprint_micro/data_sourcing.md` | 데이터 소싱 분류 + 공유 원칙 |
| `데이터저장구조.md` | DB 3계층 분리 + series_daily 스키마 |
| `backend/api/contract.md` | 현 동결 payload(리트로핏 회귀 oracle) |
| `blueprint_micro/90_open_questions.md` | 전체 미결 이슈 집계 |
