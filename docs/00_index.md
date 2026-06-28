# 문서 지도

이 폴더는 현재 운영 기준의 canonical 문서입니다. `planning/`은 아이디어와 설계의 역사, `docs/`는 지금 실제로 어떻게 돌아가는지와 앞으로 무엇을 만들지를 기록합니다.

## 먼저 읽을 문서

1. [Project Version Boundary](../PROJECT_VERSION.md)
2. [1.0 Package Manifest](1.0/00_package_manifest.md)
3. [1.0 Freeze Policy](1.0/01_freeze_policy.md)
4. [Handoff to investrader 2.0](1.0/02_handoff_to_investrader.md)
5. [프로젝트 목적과 구현 범위](01_project_purpose_and_scope.md)
6. [9단계 로드맵](02_roadmap_9_stages.md)
7. [현재 구현 인벤토리](03_current_implementation_inventory.md)
8. [Clean Architecture 리팩터링 계획](05_clean_architecture_refactor_plan.md)
9. [검증과 안전 정책](07_validation_and_safety_policy.md)
10. [테스트 전략](09_testing_strategy.md)

## 1.0 패키징

| 문서 | 책임 |
|---|---|
| [Project Version Boundary](../PROJECT_VERSION.md) | 이 repo가 1.0 reference package임을 선언 |
| [1.0 Package Manifest](1.0/00_package_manifest.md) | 1.0에 포함되는 source/runtime/doc 범위 |
| [1.0 Freeze Policy](1.0/01_freeze_policy.md) | 2.0과 섞이지 않도록 변경 허용 범위 정의 |
| [Handoff to investrader 2.0](1.0/02_handoff_to_investrader.md) | 2.0으로 가져갈 것/버릴 것/비교 기준 |
| [1.0 Reference Release Checklist](1.0/03_release_checklist.md) | 실제 tag/branch 봉인 전 체크리스트 |
| [1.0 Commit Plan](1.0/04_commit_plan.md) | 현재 변경분을 문서/기능/기타로 분리하는 커밋 계획 |

## investrader 2.0 준비 문서

| 문서 | 책임 |
|---|---|
| [Bootstrap Plan](investrader/00_bootstrap_plan.md) | 새 repo 시작 범위와 순서 |
| [Architecture Decisions](investrader/01_architecture_decisions.md) | 2.0 ADR 후보 |
| [Domain Contracts Seed](investrader/02_domain_contracts_seed.md) | 2.0 첫 domain contract 초안 |

## 단계별 문서

| 단계 | 문서 |
|---:|---|
| 1 | [증시 모멘텀과 상황 확인](stages/01_market_momentum.md) |
| 2 | [섹터별 모멘텀과 상황 확인](stages/02_sector_momentum.md) |
| 3 | [Key Player와 Rising Star 확인](stages/03_key_players_and_rising_stars.md) |
| 4 | [주요 이벤트 확인](stages/04_events.md) |
| 5 | [포트폴리오 의사결정 및 리밸런싱](stages/05_portfolio_decision_and_rebalancing.md) |
| 6 | [매수 전략 수립](stages/06_buy_strategy_planning.md) |
| 7 | [개별주 이벤트/상황 기반 매수 전략](stages/07_stock_level_event_strategy.md) |
| 8 | [매수전략 실행](stages/08_execution.md) |
| 9 | [모니터링, 리뷰, Postmortem](stages/09_monitoring_review_postmortem.md) |

## 구현 모듈 문서

| 모듈 | 문서 |
|---|---|
| Market Macro | [modules/market_macro_module.md](modules/market_macro_module.md) |
| Sector Engine | [modules/sector_engine_module.md](modules/sector_engine_module.md) |
| Stock Leadership | [modules/stock_leadership_module.md](modules/stock_leadership_module.md) |
| Event Calendar | [modules/event_calendar_module.md](modules/event_calendar_module.md) |
| Portfolio Decision | [modules/portfolio_decision_module.md](modules/portfolio_decision_module.md) |
| Buy Strategy | [modules/buy_strategy_module.md](modules/buy_strategy_module.md) |
| Execution | [modules/execution_module.md](modules/execution_module.md) |
| Monitoring & Postmortem | [modules/monitoring_postmortem_module.md](modules/monitoring_postmortem_module.md) |

## 운영/배포 문서

| 문서 | 책임 |
|---|---|
| [프로젝트 운영 개요](01_project_overview.md) | repo 정보, 현재 코드 구성 |
| [아키텍처](02_architecture.md) | 코드 레이어와 요청 흐름 |
| [데이터 파이프라인](03_data_pipeline.md) | 데이터 수집, SQLite 캐시, payload 생성 |
| [API와 KV 계약](04_api_kv_contract.md) | API endpoint와 Cloudflare KV key 계약 |
| [Cloudflare 배포](05_deployment_cloudflare.md) | Cloudflare 리소스, KV, 배포 확인 항목 |
| [GitHub Actions](06_ci_github_actions.md) | 스케줄, secrets, artifact |
| [운영 Runbook](07_operations_runbook.md) | 로컬 실행, 수동 갱신, 장애 확인 |
| [업데이트 로그](08_status_update_log.md) | 커밋된 업데이트와 현재 작업 중인 변경 |
| [미결 사항](09_open_questions.md) | 아직 결정 또는 확인이 필요한 항목 |

## ADR

아키텍처 결정은 `docs/adr/`에 별도로 둡니다.

- [ADR 0001: Cloudflare KV 정적 API 배포](adr/0001-cloudflare-kv-static-api.md)
- [ADR 0002: SQLite dashboard cache](adr/0002-sqlite-dashboard-cache.md)
