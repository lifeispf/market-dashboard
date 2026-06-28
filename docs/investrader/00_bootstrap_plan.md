# investrader 2.0 Bootstrap Plan

작성 기준일: 2026-06-28

## 프로젝트명

```text
investrader
```

## 정체성

`investrader`는 KOSPI와 NASDAQ을 대상으로 하는 clean architecture 기반 투자 의사결정 및 자동매매 시스템이다.

MVP에서는 실제 주문 실행을 제외하고, 아래 흐름까지만 구현한다.

```text
Market 판단
→ Sector 판단
→ Stock 후보 판단
→ Portfolio 목표 비중 제안
```

## 1.0과의 관계

| 프로젝트 | 역할 |
|---|---|
| `market-dashboard` 1.0 | reference, prototype, operation baseline, comparison oracle |
| `investrader` 2.0 | clean architecture 기반 신규 구현 |

1.0 코드를 그대로 복사하지 않는다. 개념, 테스트 fixture, 일부 계산식, 운영 경험만 선별해 가져간다.

## 새 repo 권장

권장 repo:

```text
github.com/lifeispf/investrader
```

권장 이유:

- 1.0과 2.0 runtime이 섞이지 않는다.
- history와 issue/PR 흐름이 명확하다.
- 자동매매 실행 계층을 별도 안전 정책으로 관리할 수 있다.

## 초기 디렉터리 구조

```text
investrader/
  apps/
    api/
    dashboard/
    jobs/
  packages/
    domain/
    data/
    engine/
    validation/
    portfolio/
    strategy/
    execution/
    observability/
  docs/
    architecture/
    adr/
    stages/
    modules/
  tests/
```

## 핵심 패키지 책임

| 패키지 | 책임 |
|---|---|
| `domain` | 공용 타입과 계약 |
| `data` | provider interface, store, schema |
| `engine` | market/sector/stock/event 판단 |
| `validation` | replay, backtest, scorecard |
| `portfolio` | 목표 비중, 리밸런싱 계획 |
| `strategy` | 진입/손절/체크아웃 rule |
| `execution` | paper trading, broker adapter 후보 |
| `observability` | run log, audit log, data freshness |

## 첫 MVP 범위

포함:

- KOSPI/NASDAQ market verdict.
- Sector verdict.
- Stock candidate verdict.
- Portfolio target allocation.
- Data freshness.
- Validation status.
- Contract tests.

제외:

- 실제 주문 실행.
- broker API.
- 자동 매수/매도.
- 검증 전 확률/승률 노출.
- 완전한 event automation.

## 1.0에서 가져갈 것

- `EngineOutput` 계열의 공용 envelope 아이디어.
- graceful degradation 원칙.
- `verified=false` / 검증 전 확률 비노출 원칙.
- Macro→Sector→Stock cascade 아이디어.
- SQLite read-through cache 경험.
- Cloudflare KV/GitHub Actions 운영 경험.
- 일부 metric 계산식과 테스트 fixture.

## 1.0에서 가져가지 않을 것

- 큰 API assembly 함수.
- frozen payload 중심 구조.
- frontend component folder 중심 구조.
- Cloudflare Worker source가 repo에 없는 운영 구조.
- 검증 전 action hint를 주문 계획처럼 취급하는 방식.

## Bootstrap 순서

1. 새 GitHub repo 생성.
2. `README.md`, `PROJECT_CHARTER.md`, `docs/architecture/00_overview.md` 작성.
3. `packages/domain`에 핵심 계약 정의.
4. `packages/data`에 schema/provider/store interface 정의.
5. `packages/engine`에 market/sector/stock skeleton 작성.
6. contract tests 작성.
7. 1.0 fixture 또는 sample payload를 oracle로 연결.
8. API와 dashboard는 domain 계약이 안정된 뒤 붙인다.

## 첫 커밋에 포함할 것

```text
README.md
PROJECT_CHARTER.md
docs/architecture/00_overview.md
docs/architecture/01_domain_contracts.md
docs/architecture/02_mvp_scope.md
packages/domain/
tests/
```

## 첫 커밋에 포함하지 않을 것

- 1.0 코드 복사본.
- broker adapter.
- 실제 주문 실행.
- Cloudflare 배포 설정.
- 복잡한 UI.
