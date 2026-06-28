# 현재 구현 인벤토리

작성 기준일: 2026-06-28

이 문서는 현재 repo에 실제로 존재하는 구현만 정리한다. 기획 문서에 있는 내용이라도 코드에 없으면 구현으로 보지 않는다.

## Backend API

| Endpoint | 파일 | 상태 | 설명 |
|---|---|---|---|
| `/api/market/{market}` | `backend/api/market.py` | Operational | frozen market payload, legacy 호환 |
| `/api/sectors/{market}` | `backend/api/sectors.py` | Partial | sector tier `EngineOutput[]` |
| `/api/stocks/{market}` | `backend/api/stocks.py` | Partial | stock tier `EngineOutput[]` |
| `/api/briefing/{market}` | `backend/api/briefing.py` | Partial | macro→sector→stock cascade summary |
| `/api/history/{market}` | `backend/api/history.py` | Partial | RRG trail, score trend, fear/greed trend |
| `/api/verification/{market}` | `backend/api/verification.py` | Partial | verification scorecard |
| `/api/health` | `backend/api/health.py` | Implemented | DB/API key readiness |

## Engine

| 영역 | 파일/폴더 | 상태 | 설명 |
|---|---|---|---|
| Engine Core | `engine/core/` | Implemented, Tested | `ModuleOutput`, `Verdict`, `EngineOutput`, `Context`, `Engine` |
| Cascade | `engine/cascade.py` | Partial, Tested | Macro→Sector→Stock 연결 |
| Macro | `engine/macro/`, `scoring.py` | Partial | 6축, fear/greed, liquidity/regime 판단 |
| Sector | `engine/sector/` | Partial, Tested | relative strength, concentration, rulebook 일부 |
| Stock | `engine/stock/` | Partial, Tested | price structure, relative strength, action hint 일부 |
| Verification | `engine/verification/` | Partial | scorecard 계산 |

## Data와 Store

| 영역 | 파일 | 상태 | 설명 |
|---|---|---|---|
| SQLite store | `backend/store/db.py` | Implemented | `series_daily`, `scores_daily`, `sector_metrics_daily`, `series_ohlc_daily` |
| Ingest helper | `backend/store/ingest.py` | Partial | read-through cache, intraday TTL, OHLC refresh |
| Data fetcher | `data/*.py` | Partial | FRED, KRX, Yahoo, manual data |
| Payload generator | `scripts/generate_payloads.py` | Operational | route function을 호출해 KV payload 생성 |

## Frontend

| 영역 | 파일/폴더 | 상태 | 설명 |
|---|---|---|---|
| App shell | `frontend/src/App.tsx` | Implemented | dashboard state와 view orchestration |
| API types | `frontend/src/api/types.ts` | Implemented | frozen payload와 EngineOutput 타입 |
| Components | `frontend/src/components/` | Partial | macro/sector/stock/decision UI |
| Primitives | `frontend/src/primitives/` | Partial | `VerdictCard`, `ModuleCard` |
| Design | `frontend/src/design/`, `frontend/src/index.css` | Partial | dashboard style layer |

## Deployment/Operations

| 영역 | 파일 | 상태 | 설명 |
|---|---|---|---|
| GitHub Actions refresh | `.github/workflows/refresh-payloads.yml` | Operational | scheduled KV payload refresh |
| Cloudflare KV upload | workflow 내 `wrangler kv bulk put` | Operational | namespace id 기준 bulk upload |
| Cloudflare Worker source | 없음 | Unknown | 현재 workspace에 Worker source/wrangler config 없음 |
| Local DB cache | `dashboard.db` | Operational | gitignore, Actions cache로 보존 |

## 현재 미커밋 작업

2026-06-28 기준으로 다음 작업이 미커밋 상태였다.

| 파일 | 작업 내용 |
|---|---|
| `.github/workflows/refresh-payloads.yml` | NASDAQ open/close phase cron 분리 |
| `scripts/generate_payloads.py` | payload 생성 전 `^IXIC` OHLC snapshot 저장 |
| `backend/store/db.py` | `series_ohlc_daily` 추가 |
| `backend/store/ingest.py` | intraday TTL과 OHLC refresh helper |
| `data/us_fetcher.py` | Yahoo OHLC fetch helper |
| `engine/tests/test_ohlc_storage.py` | open/close phase 누적 테스트 |

## 신뢰도 요약

| 영역 | 신뢰도 | 이유 |
|---|---|---|
| API shape | 중간 | 타입과 일부 테스트가 있으나 contract snapshot test가 부족 |
| 데이터 갱신 | 중간 | Operational이나 refresh status/run log가 부족 |
| Macro 판단 | 중간 | 운영 중이나 검증 게이트는 제한적 |
| Sector 판단 | 낮음~중간 | 일부 모듈만 구현 |
| Stock 판단 | 낮음~중간 | price/RS/action 일부만 구현 |
| 자동매매 실행 | 없음 | 구현 범위 밖 |

## 바로 보강할 문서/테스트

- API contract snapshot test.
- `backend/store/schema.py` 분리와 schema contract test.
- refresh status/run log 테이블.
- 현재 구현 모듈별 입력/출력/한계 문서.
