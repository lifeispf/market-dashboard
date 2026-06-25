"""engine/macro/vkospi_source.py — VKOSPI(코스피200 변동성지수) fetch via KRX OpenAPI.

KOSPI Fear&Greed의 F3(변동성)을 realized-vol 근사 대신 실제 implied-vol 지수
**VKOSPI**로 쓰기 위한 소스. VKOSPI는 KRX 파생상품지수(`idx/drvprod_dd_trd`)에
'코스피 200 변동성지수' 이름으로 제공된다 — `KRX_API_KEY` + 해당 API 활용신청 필요.

무키/미신청(401)/실패 시 None → 호출측(engine/macro/inputs.py)이 realized vol로
폴백한다(graceful degrade, 크래시 없음). eps_source.py와 동일한 비보호 사이드카
패턴이며, KRX 호출 자체는 data/krx_openapi.py의 헬퍼를 재사용한다(그 파일은 수정 안 함).
"""
from __future__ import annotations

from data import krx_openapi

# KRX 파생상품지수 OutBlock의 IDX_NM (정확 일치). 실호출로 확인됨(2026-06).
_VKOSPI_NAME = "코스피 200 변동성지수"
_EP = "/idx/drvprod_dd_trd"

# 한 프로세스(=한 생성 실행) 내 같은 날 중복 호출 방지(gather_macro_inputs가 tf마다 호출).
_cache: dict[str, float | None] = {}


def fetch_vkospi() -> float | None:
    """최근 영업일 VKOSPI 종가. 무키/미신청/실패 시 None.

    krx_openapi의 _recent_bas_dd(주말/공휴일 회피)·_get(AUTH_KEY 인증)을 재사용하고,
    파생상품지수 OutBlock에서 '코스피 200 변동성지수' 행의 CLSPRC_IDX를 뽑는다.
    """
    if not krx_openapi.is_enabled():
        return None
    from datetime import date

    day = date.today().isoformat()
    if day in _cache:
        return _cache[day]

    result: float | None = None
    for bd in krx_openapi._recent_bas_dd():
        try:
            rows = krx_openapi._get(_EP, bd)
        except krx_openapi.KrxAuthError:
            break  # 미신청 — 영업일 바꿔도 동일, 즉시 폴백
        except Exception:
            continue
        for r in rows:
            if (r.get("IDX_NM") or "").strip() == _VKOSPI_NAME:
                v = krx_openapi._to_float(r.get("CLSPRC_IDX"))
                if v is not None and v > 0:
                    result = v
                    break
        if result is not None:
            break

    _cache[day] = result
    return result
