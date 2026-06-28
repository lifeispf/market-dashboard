# ADR 0002: SQLite dashboard cache

작성 기준일: 2026-06-28

## 상태

Accepted, 운영 중

## 배경

시장 데이터는 매번 전체 lookback을 다시 fetch하면 느리고 불안정합니다. 또한 regime, RRG tail, 검증 게이트, open/close snapshot은 일별 이력이 필요합니다.

## 결정

workspace root의 `dashboard.db` SQLite 파일을 read-through cache와 계산 이력 저장소로 사용합니다.

주요 테이블:

- `series_daily`
- `series_ohlc_daily`
- `scores_daily`
- `sector_metrics_daily`

`dashboard.db`는 git에 커밋하지 않고, GitHub Actions cache로 실행 간 보존합니다.

## 결과

장점:

- Python 표준 라이브러리 `sqlite3`만으로 운영 가능합니다.
- gap fetch와 upsert로 API 호출량을 줄입니다.
- GitHub Actions cache와 잘 맞습니다.
- 향후 walk-forward 검증 데이터의 기반이 됩니다.

단점:

- Actions cache는 영구 저장소가 아니므로 완전한 운영 DB는 아닙니다.
- 동시쓰기에는 주의가 필요합니다.
- cache miss 시 초기 실행이 느릴 수 있습니다.

## 후속 작업

- OHLC snapshot이 GitHub Actions cache에서 안정적으로 누적되는지 확인합니다.
- 필요하면 `engine_verdicts` 같은 tier-agnostic verdict 이력 테이블을 추가합니다.
- 백테스트가 무거워지면 DuckDB 전환 가능성을 재검토합니다.
