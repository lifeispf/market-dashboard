# 미결 사항

작성 기준일: 2026-06-28

## 자동매매 시스템 범위

| 항목 | 상태 | 필요 조치 |
|---|---|---|
| 실제 자동 주문 지원 여부와 시점 | 미결 | paper trading과 검증 게이트 이후 결정 |
| 브로커 API 후보 | 미결 | 한국/미국 계좌별 지원 API 조사 |
| 현금/본주/2배 레버리지 비중 산식 | 미결 | macro regime 기반 보수적 rule부터 설계 |
| KOSPI/NASDAQ 배분 기준 | 미결 | market verdict 간 비교 계약 필요 |
| 전략 승인/수동 확인 흐름 | 미결 | 실제 주문 전 human approval 또는 kill switch 정책 결정 |
| postmortem schema | 미결 | trade journal, strategy id, error taxonomy 설계 |

## Cloudflare

| 항목 | 상태 | 필요 조치 |
|---|---|---|
| Worker public URL | 미확인 | Cloudflare dashboard 또는 별도 repo 확인 |
| Worker name | 미확인 | Cloudflare dashboard 확인 |
| Custom domain/route | 미확인 | DNS/Worker route 확인 |
| Worker source | 현재 workspace에 없음 | 별도 repo 또는 dashboard inline code 여부 확인 |
| Pages project | 미확인 | frontend 배포 방식 확인 |

## GitHub Actions

| 항목 | 상태 | 필요 조치 |
|---|---|---|
| `MARKET_SNAPSHOT_PHASE=open` 실제 캡처 품질 | 작업 중 | 다음 NASDAQ 개장 후 Action 결과 확인 |
| `dashboard.db` cache 연속성 | 운영 중 | cache restore와 OHLC row 누적 확인 |
| artifact 크기와 KV upload 시간 | 운영 중 | Actions 로그에서 주기적으로 확인 |

## 데이터

| 항목 | 상태 | 필요 조치 |
|---|---|---|
| KRX API quota와 장애 fallback | 부분 구현 | 장애 시 degrade 상태 확인 |
| Yahoo Finance throttling | 부분 대응 | GitHub runner에서 실패율 모니터링 |
| OHLC open/close 공식성 | 작업 중 | Yahoo open 값이 원하는 시점의 open인지 검증 |

## 문서

| 항목 | 상태 | 필요 조치 |
|---|---|---|
| Cloudflare 실제 URL | TBD | 확인 후 `05_deployment_cloudflare.md` 갱신 |
| Worker route to KV mapping | TBD | Worker code 확인 후 `04_api_kv_contract.md` 갱신 |
| 운영 담당자/계정 | TBD | 필요 시 별도 private 운영 메모에 기록 |
