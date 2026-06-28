# Market Dashboard 1.0

증시, 섹터, 종목 레이어를 하나의 decision intelligence 흐름으로 묶는 시장 대시보드입니다.

이 repo는 `investrader` 2.0을 새로 설계하고 구현하기 위한 **1.0 reference package**입니다. 현재 구현은 FastAPI 백엔드, React/Vite 프론트엔드, Python 엔진, SQLite 캐시, GitHub Actions 기반 payload 생성, Cloudflare KV 배포 흐름으로 구성되어 있습니다.

## Version Boundary

- 1.0 repo: `market-dashboard`
- 2.0 project: `investrader`
- 1.0 역할: reference, prototype, operation baseline, comparison oracle
- 2.0 역할: clean architecture 기반 투자 의사결정/자동매매 시스템

2.0 production code는 이 repo에 섞지 않습니다. 자세한 경계는 [PROJECT_VERSION.md](PROJECT_VERSION.md)와 [1.0 Package Manifest](docs/1.0/00_package_manifest.md)를 봅니다.

## 빠른 시작

```powershell
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

프론트엔드는 기본적으로 `http://localhost:5173`, 백엔드는 `http://localhost:8000`에서 실행합니다.

## 주요 문서

- [문서 지도](docs/00_index.md)
- [Project Version Boundary](PROJECT_VERSION.md)
- [1.0 Package Manifest](docs/1.0/00_package_manifest.md)
- [1.0 Freeze Policy](docs/1.0/01_freeze_policy.md)
- [Handoff to investrader 2.0](docs/1.0/02_handoff_to_investrader.md)
- [1.0 Reference Release Checklist](docs/1.0/03_release_checklist.md)
- [1.0 Commit Plan](docs/1.0/04_commit_plan.md)
- [investrader Bootstrap Plan](docs/investrader/00_bootstrap_plan.md)
- [investrader Domain Contracts Seed](docs/investrader/02_domain_contracts_seed.md)
- [프로젝트 목적과 구현 범위](docs/01_project_purpose_and_scope.md)
- [9단계 로드맵](docs/02_roadmap_9_stages.md)
- [현재 구현 인벤토리](docs/03_current_implementation_inventory.md)
- [Clean Architecture 리팩터링 계획](docs/05_clean_architecture_refactor_plan.md)
- [검증과 안전 정책](docs/07_validation_and_safety_policy.md)
- [테스트 전략](docs/09_testing_strategy.md)
- [운영 Runbook](docs/07_operations_runbook.md)
- [Cloudflare 배포](docs/05_deployment_cloudflare.md)

## 운영 기준

- GitHub repo: `https://github.com/lifeispf/market-dashboard`
- 기본 브랜치: `master`
- 배포 데이터 생성: `.github/workflows/refresh-payloads.yml`
- KV payload 생성기: `scripts/generate_payloads.py`
- 로컬 DB 캐시: `dashboard.db` (git 추적 제외)

민감한 값은 문서나 코드에 넣지 않습니다. GitHub Secrets 또는 Cloudflare 설정에만 둡니다.

## 현재 경계

최종 목표는 자동매매 시스템이지만, 현재 구현은 자동매매를 위한 시장/섹터/종목 판단과 전략 수립 기반입니다. 검증 전 산출은 매매 지시나 확률 예측이 아니라 비검증 리서치 신호로 취급합니다.
