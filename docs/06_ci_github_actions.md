# GitHub Actions

작성 기준일: 2026-06-28

## 저장소

- Repo: `https://github.com/lifeispf/market-dashboard`
- Branch: `master`
- Workflow: `.github/workflows/refresh-payloads.yml`
- Workflow name: `refresh-payloads`

## 실행 트리거

| UTC cron | KST | phase | 목적 |
|---|---:|---|---|
| `0 22 * * *` | 07:00 | `close` | 미국장 종가 정착 후 |
| `0 0 * * *` | 09:00 | `snapshot` | KOSPI 개장 직전 |
| `30 6 * * *` | 15:30 | `snapshot` | KOSPI 마감 |
| `45 13 * * *` | 22:45 | `open` | NASDAQ 개장 후 시가 캡처, 서머타임 |
| `45 14 * * *` | 23:45 | `open` | NASDAQ 개장 후 시가 캡처, 표준시 |

수동 실행:

- `workflow_dispatch`

## Job 요약

1. `actions/checkout@v4`
2. `actions/setup-python@v5`, Python `3.12`, pip cache
3. `pip install -r requirements.txt`
4. `dashboard.db` cache restore
5. schedule에 따라 `MARKET_SNAPSHOT_PHASE` 설정
6. `python scripts/generate_payloads.py --out kv_payloads.json`
7. `npx --yes wrangler@4 kv bulk put kv_payloads.json --namespace-id ... --remote`
8. `kv_payloads.json` artifact 업로드, retention 7일

## Concurrency

```yaml
concurrency:
  group: refresh-payloads
  cancel-in-progress: true
```

동시에 여러 refresh가 겹치면 이전 실행을 취소합니다.

## Cache

`dashboard.db`를 GitHub Actions cache로 보존합니다.

- Path: `dashboard.db`
- Key: `dashboard-db-${{ github.run_id }}`
- Restore key prefix: `dashboard-db-`

이 구조는 매 실행마다 새 cache를 저장하되, 다음 실행에서 가장 최근 cache를 복원하기 위한 방식입니다.

## Secrets

| Secret | 사용처 |
|---|---|
| `FRED_API_KEY` | FRED 데이터 |
| `KRX_API_KEY` | KRX OpenAPI 데이터 |
| `CLOUDFLARE_API_TOKEN` | Cloudflare KV bulk put |

Secret 값은 문서화하지 않습니다.

## 실패 시 우선 확인

- `Generate payloads` step에서 endpoint별 실패 목록이 있는지 확인합니다.
- `Upload payloads to Cloudflare KV` step에서 token 권한 또는 namespace id 오류를 확인합니다.
- `dashboard.db` cache restore 실패는 치명적이지 않지만 실행 시간이 늘고 히스토리 연속성이 약해질 수 있습니다.
- KRX 관련 값이 `null`로 degrade되면 `KRX_API_KEY` secret과 API quota를 확인합니다.
