# 업데이트 로그

작성 기준일: 2026-06-28

이 문서는 현재 운영 기준에서 중요한 업데이트만 요약합니다. 자세한 설계 배경은 `planning/`을 참조합니다.

## 최근 커밋된 업데이트

| Commit | 요약 |
|---|---|
| `6e6c333` | DI-3 Action layer: 투명 룰 기반 진입, 손절, 비중, 가드레일 |
| `e2b56c7` | DI-1/2: 섹터 룰베이스 추론, Layer3 Why/Counter 카드 |
| `d9d7980` | Layer0 Executive Summary, 룰베이스 Why/Counter-Evidence |
| `9d6db9d` | Layer1 추세차트 정직화, 측정 IC 신뢰도 배지 |
| `3b7b2a2` | Breadth 해석 5등급과 색 그라데이션 |
| `a048246` | 모든 섹터 주도주 7개, 트리맵 timeframe 기간수익률 연동 |
| `0537d46` | KOSPI level `asOf`를 KRX OpenAPI 최신점으로 보강 |
| `54588fa` | 프론트 우측 상단 갱신 시각 표시 |
| `0671e87` | Fear & Greed factor raw 측정값 표시 |
| `c238c65` | KOSPI F3 변동성을 VKOSPI로 전환 |
| `8b750cf` | GitHub Action에 `KRX_API_KEY` 전달 |
| `4d09c9a` | CI runner에서 `db.init_db()` 누락으로 인한 degrade 해결 |

## 2026-06-28 현재 작업 중인 변경

문서 작성 전 git 상태 기준으로 다음 파일이 수정 또는 추가되어 있었습니다.

| 파일 | 내용 |
|---|---|
| `.github/workflows/refresh-payloads.yml` | NASDAQ open snapshot cron 추가, schedule별 `MARKET_SNAPSHOT_PHASE` 설정 |
| `scripts/generate_payloads.py` | payload 생성 전에 NASDAQ `^IXIC` OHLC snapshot 저장 |
| `backend/store/db.py` | `series_ohlc_daily` 테이블과 OHLC upsert/read helper 추가 |
| `backend/store/ingest.py` | yfinance intraday TTL, OHLC refresh helper 추가 |
| `data/us_fetcher.py` | Yahoo Finance OHLCV fetch helper 추가 |
| `engine/tests/test_ohlc_storage.py` | open phase와 close phase가 같은 market date에 누적되는지 검증 |

## 운영상 의미

NASDAQ 장중 시가와 장마감 종가를 같은 날짜 row에 분리 저장할 수 있게 됩니다. 이 구조는 장중 open snapshot이 종가 필드를 덮어쓰는 문제를 피하고, close phase가 high/low/close/volume을 나중에 채우는 방식입니다.

## 다음 업데이트 시 기록할 것

- Cloudflare Worker 공개 URL과 route 확인.
- Worker source 또는 별도 repo 위치 확인.
- `series_ohlc_daily`가 실제 배포 Action cache에서 안정적으로 유지되는지 확인.
- `engine/tests/test_ohlc_storage.py` 커밋 여부와 테스트 결과.
