# Handoff to investrader 2.0

작성 기준일: 2026-06-28

## 목적

이 문서는 `market-dashboard` 1.0에서 `investrader` 2.0으로 무엇을 가져가고, 무엇을 버리고, 무엇을 비교 기준으로 남길지 정의한다.

## 2.0으로 가져갈 개념

| 1.0 개념 | 2.0 적용 |
|---|---|
| `EngineOutput` | `ModuleOutput`, `Verdict`, `Decision` 계약으로 확장 |
| Macro→Sector→Stock cascade | Market→Sector→Stock→Portfolio pipeline으로 확장 |
| Graceful degradation | 모든 데이터/모듈에 필수 정책 |
| `verified=false` | ValidationStatus로 확장 |
| Cloudflare KV 운영 경험 | 2.0 배포 전략 비교 후보 |
| SQLite read-through cache | 2.0 local research store 후보 |
| Frozen MarketPayload | 2.0 비교 oracle |

## 2.0으로 직접 가져가지 않을 코드

| 1.0 요소 | 이유 |
|---|---|
| `backend/api/market.py`의 큰 assembly 함수 | 2.0에서는 application use case로 재설계 |
| UI component 구조 전체 | 2.0에서는 feature slice로 재설계 |
| Cloudflare Worker source 부재 구조 | 2.0에서는 배포 코드를 repo 안에 둔다 |
| 검증 전 action hint | 2.0에서는 portfolio/strategy/execution gate 분리 |
| 자동매매 실행을 1.0에 덧붙이는 방식 | 경계 혼합 위험 |

## 2.0에서 새로 정의할 계약

- `ModuleOutput`
- `Verdict`
- `Decision`
- `PortfolioTarget`
- `OrderPlan`
- `ExecutionResult`
- `Postmortem`
- `DataFreshness`
- `ValidationStatus`
- `RunLog`
- `AuditEvent`

## 1.0을 oracle로 사용하는 방법

2.0 구현 중 다음을 1.0과 비교한다.

| 비교 대상 | 기준 |
|---|---|
| Market regime | `/api/market/{market}`와 `/api/briefing/{market}` |
| Sector ranking | `/api/sectors/{market}` |
| Stock candidates | `/api/stocks/{market}` |
| Data freshness | `generatedAt`, `freshness`, DB latest date |
| KV payload key | `scripts/generate_payloads.py` 결과 |

목표는 항상 동일한 결과를 만드는 것이 아니다. 1.0과 다르게 판단한다면 그 이유를 문서화하고 테스트해야 한다.

## 2.0 MVP 경계

`investrader` 2.0 MVP는 다음까지만 구현한다.

```text
Market 판단
→ Sector 판단
→ Stock 후보 판단
→ Portfolio 목표 비중 제안
```

MVP에서 제외:

- 실제 주문 실행.
- 브로커 API 연동.
- 자동 매수/매도.
- 검증 전 확률/승률 노출.

## 새 repo 권장 구조

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
```
