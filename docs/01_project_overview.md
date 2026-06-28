# 프로젝트 개요

작성 기준일: 2026-06-28

## 한 줄 설명

KOSPI와 NASDAQ을 대상으로 macro, sector, stock 판단 레이어를 연결해 시장 상태와 행동 가이드를 보여주는 decision intelligence dashboard입니다.

## 저장소

- GitHub repo: `https://github.com/lifeispf/market-dashboard`
- 현재 브랜치: `master`
- 원격: `origin`
- 현재 배포 데이터 생성 workflow: `.github/workflows/refresh-payloads.yml`

## 현재 코드 구성

| 영역 | 경로 | 역할 |
|---|---|---|
| Backend | `backend/` | FastAPI entrypoint, API router, DB store |
| Engine | `engine/` | macro, sector, stock, cascade 판단 엔진 |
| Data | `data/` | FRED, KRX, Yahoo 등 데이터 fetcher |
| Frontend | `frontend/` | React/Vite dashboard UI |
| Scripts | `scripts/` | Cloudflare KV payload 생성 등 운영 스크립트 |
| Planning | `planning/` | 기획, 블루프린트, 원본 설계 문서 |
| Docs | `docs/` | 현재 운영 기준 문서 |

## 제품 범위

현재 앱은 다음 흐름을 중심으로 구성됩니다.

1. Macro layer: 시장 전체 유동성, 레짐, 공포탐욕, ceiling, reconciliation.
2. Sector layer: 섹터 상대강도, 섹터 랭킹, 섹터별 narrative.
3. Stock layer: 섹터 내 주요 종목, 가격 구조와 상대강도 기반 판단.
4. Decision layer: 투명한 룰 기반 행동 레이어, 진입/손절/비중 가드레일.

## 운영 형태

로컬 개발에서는 FastAPI와 Vite dev server를 직접 실행합니다.

배포 운영에서는 GitHub Actions가 Python 엔진을 실행해 API 응답 payload를 미리 만들고, `wrangler kv bulk put`으로 Cloudflare KV에 업로드합니다. Cloudflare Worker 또는 edge endpoint는 KV key를 읽어 정적 API처럼 응답하는 구조로 추정됩니다. Worker 공개 URL과 Cloudflare project 이름은 현재 repo 안에서 확인되지 않았습니다.

## 민감 정보 원칙

다음 값은 이름만 문서화하고 실제 값은 기록하지 않습니다.

- `FRED_API_KEY`
- `KRX_API_KEY`
- `CLOUDFLARE_API_TOKEN`
- Cloudflare account id, token value, route secret
