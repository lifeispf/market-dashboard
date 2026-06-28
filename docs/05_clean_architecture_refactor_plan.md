# Clean Architecture 리팩터링 계획

작성 기준일: 2026-06-28

이 문서는 `sector-radar` MVP repo 검토에서 차용할 만한 구조를 현재 프로젝트에 맞게 적용하기 위한 계획이다.

## 목표

현재 프로젝트는 기능이 빠르게 늘어나면서 `backend/api`, `engine`, `store`, `frontend/components`가 동시에 커지고 있다. 자동매매 시스템으로 확장하려면 모듈 경계, 데이터 계약, 테스트 계약을 더 단단하게 만들어야 한다.

## 차용할 원칙

| 원칙 | 적용 방향 |
|---|---|
| Domain model은 작고 독립적으로 둔다 | `engine/core/contracts.py`를 기준 계약으로 유지 |
| Application use case를 둔다 | API router가 직접 조립하지 않도록 `backend/application/` 또는 `engine/application/` 추가 |
| Schema는 canonical 파일로 분리한다 | `backend/store/schema.py`에 DDL과 column constants 배치 |
| Refresh 상태를 1급 데이터로 둔다 | `data_refresh_status`, `run_log` 추가 |
| JSON/API contract를 테스트한다 | snapshot/shape tests 추가 |
| Frontend는 feature slice로 정리한다 | macro/sector/stock/decision별 `features/` 분리 |

## 제안 디렉토리

```text
backend/
  application/
    build_market_payload.py
    build_sector_response.py
    build_stock_response.py
    build_briefing_response.py
    refresh_payloads.py
  store/
    schema.py
    db.py
    ingest.py

frontend/src/
  features/
    macro/
    sector/
    stock/
    decision/
  primitives/
  api/
```

## 1단계: Store schema 분리

현재:

- `backend/store/db.py` 안에 DDL과 DB helper가 함께 있다.

개선:

- `backend/store/schema.py` 생성.
- `DDL_STATEMENTS`, 테이블별 컬럼 상수를 정의.
- `db.init_db()`는 schema 상수를 실행만 한다.

추가 테스트:

- schema가 필요한 테이블을 모두 포함하는지.
- `series_ohlc_daily` open/close phase upsert가 깨지지 않는지.

## 2단계: Refresh status/run log 추가

차용 대상:

- `sector-radar`의 `data_refresh_status`, `run_log`.

우리 프로젝트 적용:

- GitHub Action 또는 local payload 생성이 다음 정보를 기록한다.

```text
provider / runner
status
phase(open/close/snapshot)
last_attempt_at
last_success_at
latest_price_date
rows_written
keys_generated
message
```

기대 효과:

- 프론트에서 `generatedAt`뿐 아니라 데이터 연결 상태를 보여줄 수 있다.
- Action 실패와 partial degrade를 원인별로 추적할 수 있다.

## 3단계: Application use case 추가

현재:

- `backend/api/market.py`의 `assemble_payload()`.
- 각 API router가 engine 호출과 response 조립을 직접 수행.

개선:

- router는 HTTP parameter validation과 response 반환만 담당.
- 실제 조립은 application use case로 이동.

예:

```text
backend/api/sectors.py
  -> backend/application/build_sector_response.py
      -> engine/sector/*
      -> backend/store/*
```

## 4단계: Contract tests 추가

추가할 테스트:

- frozen `MarketPayload` shape test.
- `EngineOutput` shape test.
- `/api/briefing` response shape test.
- Cloudflare KV key generation test.
- schema constant contract test.

목표:

- 리팩터링해도 API와 KV payload 계약이 깨지지 않도록 한다.

## 5단계: Frontend feature slice

현재:

- `frontend/src/components/`에 화면 컴포넌트가 집중되어 있다.

개선:

```text
frontend/src/features/macro/
frontend/src/features/sector/
frontend/src/features/stock/
frontend/src/features/decision/
```

각 feature는 다음을 가진다.

- `model.ts`: 정렬, grouping, label, formatter 같은 순수 helper.
- `components/`: 화면 컴포넌트.
- `types.ts`는 가능하면 `frontend/src/api/types.ts`의 공용 타입을 import.

## 적용 우선순위

1. `backend/store/schema.py` 분리.
2. refresh status/run log 테이블 추가.
3. API/KV contract tests.
4. application use case 계층.
5. frontend feature slice.

## 차용하지 않을 것

- `sector-radar`의 stdlib HTTP local server. 현재 프로젝트는 FastAPI 유지.
- D1/Scheduled Worker로 즉시 전환. 현재는 GitHub Actions + Cloudflare KV 유지.
- Python metric과 TypeScript Worker metric의 중복 구현. 현재 프로젝트는 Python engine을 source of truth로 둔다.
