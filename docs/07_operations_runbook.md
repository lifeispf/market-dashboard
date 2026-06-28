# 운영 Runbook

작성 기준일: 2026-06-28

## 로컬 실행

Backend:

```powershell
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

기본 URL:

- Backend: `http://localhost:8000`
- FastAPI docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

## 로컬 payload 생성

```powershell
python scripts/generate_payloads.py --out kv_payloads.json
```

NASDAQ open snapshot을 강제로 테스트:

```powershell
$env:MARKET_SNAPSHOT_PHASE="open"
python scripts/generate_payloads.py --out kv_payloads.json
```

NASDAQ close snapshot을 강제로 테스트:

```powershell
$env:MARKET_SNAPSHOT_PHASE="close"
python scripts/generate_payloads.py --out kv_payloads.json
```

## 수동 배포 갱신

1. GitHub repo의 Actions 탭으로 이동합니다.
2. `refresh-payloads` workflow를 선택합니다.
3. `Run workflow`로 수동 실행합니다.
4. `Generate payloads`와 `Upload payloads to Cloudflare KV` step 성공 여부를 확인합니다.
5. 프론트에서 갱신 시각(`generatedAt`)이 바뀌었는지 확인합니다.

## 수동 KV 업로드

Cloudflare token이 로컬 환경에 설정되어 있을 때만 실행합니다.

```powershell
python scripts/generate_payloads.py --out kv_payloads.json
npx --yes wrangler@4 kv bulk put kv_payloads.json --namespace-id 12dd9f0b4bba435db6e1ad0f43ab1b06 --remote
```

## DB 초기화

`dashboard.db`는 재생성 가능한 캐시입니다. 다만 삭제하면 히스토리와 warm cache가 사라집니다.

스키마만 보장하려면:

```powershell
python -c "from backend.store import db; db.init_db()"
```

## 자주 보는 증상

| 증상 | 먼저 볼 곳 |
|---|---|
| 프론트 갱신 시각이 바뀌지 않음 | GitHub Actions 최신 실행, KV upload step |
| `no such table: series_daily` | `scripts/generate_payloads.py`에서 `db.init_db()` 호출 여부 |
| KOSPI breadth 또는 VKOSPI 값이 비어 있음 | `KRX_API_KEY`, KRX API 상태 |
| NASDAQ open/close가 같은 날 누적되지 않음 | `MARKET_SNAPSHOT_PHASE`, `series_ohlc_daily` row |
| payload 파일이 너무 오래됨 | Actions artifact와 KV key 갱신 시각 |

## 테스트

현재 repo에는 engine 테스트가 있습니다.

```powershell
python -m unittest discover engine/tests
```

Frontend build:

```powershell
cd frontend
npm run build
```
