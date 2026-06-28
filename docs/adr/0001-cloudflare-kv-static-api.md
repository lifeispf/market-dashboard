# ADR 0001: Cloudflare KV 정적 API 배포

작성 기준일: 2026-06-28

## 상태

Accepted, 운영 중

## 배경

시장 dashboard는 외부 데이터 fetch와 Python 계산이 필요합니다. Cloudflare Free Worker에서 이 계산을 직접 수행하기보다, GitHub Actions runner에서 payload를 미리 생성하고 Cloudflare KV에 올리는 방식이 현재 구조와 비용 조건에 맞습니다.

## 결정

GitHub Actions가 `scripts/generate_payloads.py`를 실행해 API 응답 payload를 생성하고, `wrangler kv bulk put`으로 Cloudflare KV에 업로드합니다. Cloudflare edge endpoint는 KV key를 읽어 API처럼 응답합니다.

## 결과

장점:

- 서버 비용과 runtime 부담이 작습니다.
- FastAPI route function을 그대로 호출하므로 로컬 API와 배포 payload의 코드 경로가 가깝습니다.
- GitHub Actions schedule로 시장 시간대별 snapshot을 만들 수 있습니다.

단점:

- 실시간 API가 아니라 snapshot API입니다.
- Cloudflare Worker source가 repo에 없으면 운영 추적성이 떨어집니다.
- KV key contract가 깨지면 Worker와 frontend가 동시에 영향을 받습니다.

## 후속 작업

- Worker source 위치를 문서화합니다.
- Worker public URL과 route를 `docs/05_deployment_cloudflare.md`에 추가합니다.
- KV key mapping을 Worker code 기준으로 검증합니다.
