# 모듈: Market Macro

## 역할

KOSPI와 NASDAQ의 전체 시장 상태를 판단한다. 하위 sector, stock, portfolio 판단의 상위 context가 된다.

## 현재 상태

상태: Partial, Operational.

## 주요 파일

- `backend/api/market.py`
- `backend/api/briefing.py`
- `engine/macro/`
- `engine/cascade.py`
- `scoring.py`
- `config.json`

## 입력

- 지수 가격과 변화율.
- FRED/KRX/Yahoo 기반 macro series.
- manual override.
- fear/greed factor.
- 섹터/리더십 보조 데이터.

## 출력

- frozen `MarketPayload`.
- macro `EngineOutput`.
- market regime.
- liquidity source states.
- reconciliation.
- narrative, risks, watchlist, freshness.

## 한계

- 일부 지표는 데이터 미가용 시 `null`로 degrade된다.
- 판단이 검증된 매매 신호라는 의미는 아니다.
- portfolio allocation으로 바로 연결되는 표준 계약은 아직 없다.

## 다음 개선

- macro application use case 분리.
- `verified`와 validation status를 더 명확히 노출.
- market verdict를 portfolio decision input으로 표준화.
