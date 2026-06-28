# Cloudflare 배포

작성 기준일: 2026-06-28

## 현재 확인된 Cloudflare 정보

| 항목 | 값 |
|---|---|
| KV namespace id | `12dd9f0b4bba435db6e1ad0f43ab1b06` |
| KV 업로드 명령 | `npx --yes wrangler@4 kv bulk put kv_payloads.json --namespace-id 12dd9f0b4bba435db6e1ad0f43ab1b06 --remote` |
| API token secret 이름 | `CLOUDFLARE_API_TOKEN` |
| payload 파일 | `kv_payloads.json` |

## 현재 repo에서 확인되지 않은 항목

다음 값은 Cloudflare dashboard, 별도 Worker repo, 또는 배포 계정에서 확인해야 합니다.

| 항목 | 상태 |
|---|---|
| Cloudflare account id | TBD |
| Worker name | TBD |
| Worker public URL | TBD |
| Custom domain 또는 route | TBD |
| Pages project name | TBD |
| Worker source 위치 | 현재 workspace에 없음 |
| `wrangler.toml` 또는 `wrangler.jsonc` | 현재 workspace에 없음 |

## 배포 모델

현재 repo 기준으로 확인되는 배포 모델은 다음과 같습니다.

1. GitHub Actions가 정해진 시간에 실행됩니다.
2. Python dependencies를 설치합니다.
3. `dashboard.db` cache를 restore합니다.
4. `scripts/generate_payloads.py`로 모든 KV payload를 생성합니다.
5. `wrangler kv bulk put`으로 Cloudflare KV에 업로드합니다.
6. Cloudflare edge endpoint가 KV에서 key를 읽어 API처럼 응답합니다.

Worker source가 현재 workspace에 없으므로 6번은 `scripts/generate_payloads.py` 주석과 key contract를 기준으로 한 운영 추정입니다.

## Secret 관리

문서에는 secret 이름만 기록합니다. 실제 값은 GitHub repository secrets 또는 Cloudflare dashboard에만 저장합니다.

필요한 GitHub Secrets:

- `CLOUDFLARE_API_TOKEN`
- `FRED_API_KEY`
- `KRX_API_KEY`

## 확인 절차

Cloudflare 배포 상태를 점검할 때는 다음 순서로 확인합니다.

1. GitHub Actions `refresh-payloads` 최신 실행 성공 여부.
2. Artifact `kv_payloads` 생성 여부.
3. `wrangler kv bulk put` step 성공 여부.
4. Cloudflare KV namespace의 key 갱신 시각.
5. Worker public URL에서 `/api/health` 또는 해당 health route 응답.
6. 프론트에서 `generatedAt` 갱신 시각 표시.
