# 데이터 파이프라인

작성 기준일: 2026-06-28

## 핵심 흐름

1. `data/*.py` fetcher가 시장 데이터를 가져옵니다.
2. `backend/store/ingest.py`가 최신 저장일을 확인하고 필요한 gap만 fetch합니다.
3. `backend/store/db.py`가 `dashboard.db`에 upsert합니다.
4. `engine/*`와 `backend/api/*`가 DB와 설정 파일을 읽어 payload를 만듭니다.
5. `scripts/generate_payloads.py`가 route function을 직접 호출해 Cloudflare KV bulk 파일을 생성합니다.
6. GitHub Actions가 `kv_payloads.json`을 Cloudflare KV에 업로드합니다.

## 저장소

SQLite 파일:

- `dashboard.db`

Git 추적 제외:

- `*.db`
- `*.db-shm`
- `*.db-wal`

## 주요 테이블

| 테이블 | 역할 |
|---|---|
| `series_daily` | 모든 일별 시계열의 long-format 저장소 |
| `series_ohlc_daily` | 일별 OHLCV, open/close phase 분리 저장 |
| `scores_daily` | 시장별 S01-S06, composite, regime 이력 |
| `sector_metrics_daily` | 섹터별 market cap, YTD, RRG 지표 이력 |

`series_ohlc_daily`는 2026-06-28 작업 기준으로 추가 중인 구조입니다. NASDAQ `^IXIC` open/close snapshot을 같은 market date에 누적하기 위한 테이블입니다.

## OHLC phase

`MARKET_SNAPSHOT_PHASE` 값에 따라 `scripts/generate_payloads.py`가 NASDAQ OHLC를 다르게 저장합니다.

| phase | 의미 | 저장 동작 |
|---|---|---|
| `open` | NASDAQ 개장 후 시가 캡처 | `open`, `open_fetched_at`만 갱신 |
| `close` | 미국장 종가 정착 후 캡처 | `high`, `low`, `close`, `volume`, `close_fetched_at` 갱신 |
| unset 또는 기타 | 일반 snapshot | 가능한 OHLC 필드 전체 갱신 |

## 주요 환경 변수

| 이름 | 사용처 | 설명 |
|---|---|---|
| `FRED_API_KEY` | 데이터 fetch | FRED 데이터 |
| `KRX_API_KEY` | 데이터 fetch | KRX OpenAPI |
| `MARKET_SNAPSHOT_PHASE` | payload 생성 | `open`, `close`, 일반 snapshot 분기 |
| `SERIES_INTRADAY_REFRESH_TTL_MINUTES` | read-through cache | yfinance intraday 재조회 TTL, 기본 180분 |

## 산출물

- `kv_payloads.json`: Cloudflare KV bulk put 입력 파일
- Git 추적 제외, 매 실행 재생성 가능
- GitHub Actions artifact로 7일 보관
