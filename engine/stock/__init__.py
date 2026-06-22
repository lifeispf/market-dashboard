"""engine.stock — Stage 5 retrofit of individual-stock analysis onto Engine Core.

정본: planning/blueprint_unified/00_architecture.md §4/§11,
blueprint_micro/stock_engine/, 01_altitude_separation.md(고도 분리 — leaders→Stock).

기존 macro payload의 `leaders` 블록(개별주 — sectors.json의 key/star 종목)을
Stock tier로 끌어올린다. entity는 ticker.

이 단계 범위: **Price 레이어**만 구현 — §35 Relative Strength(Market RS, 종목 vs
지수, scoring RRG 재사용)와 §34 Price Structure(추세·변동성·200MA). Fundamental
레이어(§31 Quality)·Market 레이어(§32 Expectation/§33 Positioning)는 데이터 평면
(§11 3단계: SEC·FINRA·Finnhub)이 들어온 뒤 추가 — 그 전까지는 모듈에서 제외(연기).
§36 Participation은 거래량 데이터(현 close-only 시리즈에 없음) 필요 → 함께 연기.

레거시 `leaders`는 byte-identical 위해 동결 payload에 잠정 유지(market.py
_assemble_sectors_leaders). 본 Stock 엔진은 같은 종목들에 해석(Verdict) 레이어를
얹어 신규 /api/stocks 엔드포인트로 노출한다.
"""
