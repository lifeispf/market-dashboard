# 1.0 Package Manifest

작성 기준일: 2026-06-28

## 패키지 정체성

```text
Package name: market-dashboard 1.0
Role: reference / prototype / operation baseline
Next project: investrader 2.0
```

1.0은 자동매매 시스템의 최종 구현이 아니다. KOSPI/NASDAQ 시장 판단, 섹터 판단, 종목 후보 판단, Cloudflare KV 운영 방식을 실험하고 축적한 reference package다.

## 포함 범위

| 영역 | 경로 | 1.0 역할 |
|---|---|---|
| Backend API | `backend/` | FastAPI endpoint와 payload assembly |
| Engine | `engine/` | macro, sector, stock, cascade 판단 엔진 |
| Data | `data/` | FRED, KRX, Yahoo, manual fetcher |
| Store | `backend/store/` | SQLite cache와 ingest helper |
| Frontend | `frontend/` | React/Vite dashboard |
| Scripts | `scripts/` | KV payload generation |
| Operations | `.github/workflows/refresh-payloads.yml` | GitHub Actions 기반 refresh |
| Config | `config.json`, `sectors.json` | 판단값과 수동 콘텐츠 |
| Docs | `docs/`, `planning/` | 현재 운영 문서와 설계 이력 |

## 제외 또는 생성물

다음은 source package로 보지 않는다.

| 항목 | 이유 |
|---|---|
| `dashboard.db` | 실행 중 생성되는 SQLite cache |
| `*.db-shm`, `*.db-wal` | SQLite runtime artifact |
| `kv_payloads.json` | KV upload용 생성 파일 |
| `.env` | 로컬 secret |
| `.venv/` | 로컬 Python 가상환경 |
| `node_modules/`, `frontend/dist/` | frontend build artifact |

## 운영 Entry Points

Local backend:

```powershell
uvicorn backend.main:app --reload --port 8000
```

Local frontend:

```powershell
cd frontend
npm.cmd run dev
```

KV payload generation:

```powershell
python scripts/generate_payloads.py --out kv_payloads.json
```

Tests:

```powershell
python -m unittest discover engine/tests
```

## 주요 API

- `/api/market/{market}`
- `/api/sectors/{market}`
- `/api/stocks/{market}`
- `/api/briefing/{market}`
- `/api/history/{market}`
- `/api/verification/{market}`
- `/api/health`

## 현재 상태

1.0은 다음 상태로 봉인한다.

| 영역 | 상태 |
|---|---|
| Market 판단 | Partial, Operational |
| Sector 판단 | Partial |
| Stock 후보 판단 | Partial |
| Portfolio decision | Partial |
| Event module | Planned |
| Execution | Not implemented |
| Monitoring/postmortem | Planned |

## 1.0의 책임

- 현재 기능을 유지한다.
- 2.0 설계의 비교 기준으로 남는다.
- 2.0이 대체할 때까지 reference UI와 payload를 제공한다.
- 새로운 자동매매 production code를 직접 수용하지 않는다.
