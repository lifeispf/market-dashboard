# investrader 2.0 Architecture Decisions

작성 기준일: 2026-06-28

## ADR 후보

2.0 새 repo를 만들 때 아래 결정을 ADR로 남긴다.

## ADR-001: 1.0 rewrite가 아니라 clean-room 2.0

결정:

- `market-dashboard` 1.0은 reference로 남긴다.
- `investrader` 2.0은 별도 repo에서 clean architecture로 시작한다.

이유:

- 1.0은 빠른 실험과 운영 경험이 섞여 있다.
- 자동매매 시스템은 domain, validation, execution 경계가 처음부터 필요하다.
- 기존 코드를 부분 리팩터링하는 방식은 1.0/2.0 경계를 흐릴 수 있다.

## ADR-002: Domain contracts first

결정:

- API, UI, engine 구현 전에 domain 계약을 먼저 정의한다.

초기 계약:

- `ModuleOutput`
- `Verdict`
- `Decision`
- `PortfolioTarget`
- `OrderPlan`
- `ExecutionResult`
- `ValidationStatus`
- `DataFreshness`
- `RunLog`
- `AuditEvent`

## ADR-003: Execution is gated

결정:

- 실제 주문 실행은 MVP에 포함하지 않는다.
- execution package는 처음에는 interface와 paper trading만 허용한다.

필수 게이트:

- historical validation.
- paper trading.
- risk limits.
- kill switch.
- duplicate order prevention.
- audit log.

## ADR-004: Python engine is source of truth

결정:

- 2.0 초기에는 Python engine을 판단 계산의 source of truth로 둔다.
- TypeScript/Worker 쪽에 같은 metric을 중복 구현하지 않는다.

이유:

- 계산 drift를 줄인다.
- 검증과 연구를 같은 코드 경로에서 수행한다.

## ADR-005: Validation status is first-class

결정:

- 모든 verdict/decision은 validation status를 포함한다.
- 검증 전 확률/승률은 노출하지 않는다.

## ADR-006: Observability is part of MVP

결정:

- `run_log`, `data_refresh_status`, `audit_log`를 MVP부터 둔다.

이유:

- 자동매매 시스템은 판단의 결과뿐 아니라 판단이 생성된 과정이 추적 가능해야 한다.
