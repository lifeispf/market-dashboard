"""engine/macro/kospi_level_source.py — KOSPI 지수 레벨의 최신 포인트를 KRX OpenAPI로 보강.

KOSPI 레벨 *시리즈*(asOf를 결정)는 kr_fetcher.fetch_kospi_level_series가
pykrx→Yahoo(^KS11)로 폴백하는데, GitHub Actions 같은 데이터센터 IP에서 yfinance는
하루~이틀 묵은 값을 준다(잘 알려진 Yahoo throttling). 반면 KRX OpenAPI(AUTH_KEY)는
키 기반이라 CI에서도 최신 영업일 종가를 안정적으로 준다.

이 사이드카는 그 최신 (값, 날짜)만 반환한다 — 호출측(engine/macro/inputs.py)이
시리즈 마지막 날짜보다 더 최신일 때만 in-memory로 한 점을 덧붙여 asOf/level/모멘텀을
신선화한다. 무키/미신청/실패 시 None → 보강 없이 기존 시리즈 그대로(graceful degrade).

vkospi_source.py와 동일한 비보호 사이드카 패턴이며 data/krx_openapi.py는 수정하지
않는다(헬퍼 fetch_kospi_level만 재사용). test_macro_equivalence는 이 함수를 None으로
monkeypatch해 동결 오라클(realized 시리즈 그대로)과 byte-identical 게이트를 유지한다.
"""
from __future__ import annotations

from datetime import date

from data import krx_openapi

# 한 프로세스(=한 생성 실행) 내 같은 날 중복 호출 방지(gather_macro_inputs가 tf마다 호출).
_cache: dict[str, tuple[float, date] | None] = {}


def fetch_latest_kospi_level() -> tuple[float, date] | None:
    """최근 영업일 KOSPI 지수 종가 (값, 날짜). 무키/미신청/실패 시 None.

    data/krx_openapi.fetch_kospi_level()을 그대로 재사용(그 파일 무수정)."""
    if not krx_openapi.is_enabled():
        return None

    day = date.today().isoformat()
    if day in _cache:
        return _cache[day]

    try:
        result = krx_openapi.fetch_kospi_level()  # (close, date) | None
    except Exception:
        result = None

    _cache[day] = result
    return result
