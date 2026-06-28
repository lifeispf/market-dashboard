# investrader 2.0 Domain Contracts Seed

작성 기준일: 2026-06-28

이 문서는 새 repo에서 첫 domain contract를 작성하기 위한 seed다. 실제 타입은 2.0 repo에서 구현한다.

## ValidationStatus

```text
unvalidated
fixture_tested
historical_tested
calibrated
paper_tested
live_approved
```

## ModuleOutput

```text
module_id
tier
entity_id
state
transition
strength
confidence
evidence
warnings
freshness
validation_status
```

## Verdict

```text
tier
entity_id
direction
strength
conviction_label
lead_pattern
narrative
risks
invalidation
horizon
validation_status
source_modules
```

## Decision

```text
decision_id
scope
subject
action
reason
constraints
validation_status
created_at
```

예:

```text
scope = portfolio
subject = NASDAQ
action = increase_weight
```

## PortfolioTarget

```text
target_id
cash_weight
market_weights
sector_weights
instrument_weights
leverage_policy
risk_limits
source_decisions
validation_status
```

## OrderPlan

```text
plan_id
portfolio_target_id
orders
preflight_checks
risk_limits
requires_approval
validation_status
```

MVP에서는 `OrderPlan`을 실제 주문으로 실행하지 않는다.

## ExecutionResult

```text
execution_id
plan_id
mode: paper | live
orders_submitted
orders_filled
orders_rejected
errors
audit_events
```

## Postmortem

```text
postmortem_id
strategy_id
decision_id
position_id
outcome
what_happened
what_worked
what_failed
rule_changes
created_at
```

## DataFreshness

```text
source
series_id
latest_date
fetched_at
stale
warnings
```

## RunLog

```text
run_id
run_type
phase
started_at
finished_at
status
message
artifacts
```

## AuditEvent

```text
event_id
actor
action
target
payload
created_at
```
