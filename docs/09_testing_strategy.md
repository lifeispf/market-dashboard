# 테스트 전략

작성 기준일: 2026-06-28

## 목표

자동매매 시스템으로 확장하기 전에 데이터, API 계약, 판단 룰, refresh 운영을 테스트로 고정한다.

## 테스트 계층

| 계층 | 목적 | 예시 |
|---|---|---|
| Unit | 순수 계산 함수 검증 | RS, RRG, breadth, action rule |
| Store | DB upsert와 query 검증 | `series_daily`, `series_ohlc_daily` |
| Contract | API/KV shape 고정 | `MarketPayload`, `EngineOutput` |
| Integration | fixture→DB→engine→API 흐름 | sector snapshot, briefing |
| Operations | refresh phase와 failure 동작 | GitHub Action payload generation |
| Validation | 과거 성과 검증 | hit-rate, IC, drawdown |

## sector-radar에서 차용할 테스트 패턴

1. Clean architecture contract test.
2. DB upsert idempotency test.
3. API JSON shape snapshot test.
4. Refresh rate-limit/failure preserve test.
5. Public refresh disabled 또는 execution disabled 정책 test.

## 우리 프로젝트에 추가할 우선 테스트

| 테스트 | 목적 |
|---|---|
| `test_store_schema_contract.py` | schema 상수와 테이블 존재 확인 |
| `test_market_payload_contract.py` | frozen market payload shape 고정 |
| `test_engine_output_contract.py` | tier 공용 envelope shape 고정 |
| `test_kv_payload_keys.py` | Cloudflare KV key 목록 고정 |
| `test_refresh_status.py` | refresh phase/open/close 기록 검증 |
| `test_briefing_contract.py` | macro→sector→stock briefing shape 고정 |

## 현재 실행 명령

```powershell
python -m unittest discover engine/tests
```

Frontend:

```powershell
cd frontend
npm.cmd run build
```

PowerShell 실행 정책 때문에 `npm` 대신 `npm.cmd`를 사용한다.

## 향후 Python 테스트 환경

권장:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python -m pip install -U pip
.\.venv312\Scripts\python -m pip install -r requirements.txt
```

pytest 기반 테스트를 추가할 경우:

```powershell
.\.venv312\Scripts\python -m pip install pytest
.\.venv312\Scripts\python -m pytest
```

## Definition of Done

새 기능 또는 리팩터링은 아래를 만족해야 한다.

- 관련 테스트 추가 또는 업데이트.
- 데이터 미가용/unknown 처리.
- 문서 업데이트.
- 검증 전 확률 노출 금지.
- API/KV 계약 변경 시 contract 문서 갱신.
