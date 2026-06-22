"""data/krx_openapi.py — KRX 정보데이터시스템 OpenAPI 클라이언트.

data.krx.co.kr OpenAPI(서비스 호스트 data-dbg.krx.co.kr)는 AUTH_KEY 헤더 인증으로
일별 스냅샷 데이터를 JSON(`{"OutBlock_1": [...]}`)으로 제공한다. pykrx(공개 페이지
스크래핑)가 종종 빈 응답("Expecting value...")으로 막히는 것을 대체하기 위한 1차
소스다.

⚠️ **검증 필요(오프라인 작성)**: 아래 엔드포인트 경로(BLD)와 필드명은 KRX OpenAPI
문서 기준의 일반적 구조다. 실제 응답 필드명이 다를 수 있으므로 필드 접근은
방어적으로(여러 후보 키 시도) 처리하고, 실패하면 None을 반환해 호출측이 pykrx/
yfinance로 폴백하게 한다. 네트워크 가능한 환경에서 `verify_krx_openapi()`로 1회
실호출 검증 후 필드명을 확정할 것.

무키/실패 시 전부 graceful degrade(None/예외) — 절대 크래시로 전파하지 않는다.
"""
from __future__ import annotations

import os
from datetime import date, timedelta

import requests

BASE_URL = "http://data-dbg.krx.co.kr/svc/apis"

# BLD(엔드포인트) — KRX OpenAPI 문서 기준. 실호출로 검증 필요.
EP_KOSPI_INDEX = "/idx/kospi_dd_trd"   # 코스피 지수 일별
EP_KOSPI_STOCKS = "/sto/stk_bydd_trd"  # 유가증권(KOSPI) 종목 일별매매

_TIMEOUT = 10


def api_key() -> str | None:
    return os.environ.get("KRX_API_KEY") or None


def is_enabled() -> bool:
    return bool(api_key())


class KrxAuthError(RuntimeError):
    """키는 인식되나 해당 API 사용 권한 없음(KRX 포털 '활용신청' 필요) 등 인증 거부.

    이 오류가 나면 다른 영업일로 재시도해도 동일하므로 호출측은 즉시 폴백한다.
    """


def _get(path: str, bas_dd: str) -> list[dict]:
    """OpenAPI GET → OutBlock_1 리스트. 키 없거나 실패 시 예외.

    인증 거부(401)는 KrxAuthError로 올려 호출측이 영업일 재시도 없이 즉시
    폴백하게 한다(미신청 API는 어느 날짜로도 통과 못 함)."""
    key = api_key()
    if not key:
        raise KrxAuthError("KRX_API_KEY 미설정")
    resp = requests.get(
        f"{BASE_URL}{path}",
        headers={"AUTH_KEY": key},
        params={"basDd": bas_dd},
        timeout=_TIMEOUT,
    )
    if resp.status_code == 401:
        raise KrxAuthError(f"401 {resp.text[:120]} (KRX OpenAPI 해당 API 활용신청 필요)")
    resp.raise_for_status()
    data = resp.json()
    block = data.get("OutBlock_1")
    if not isinstance(block, list):
        raise ValueError(f"예상치 못한 응답 형태: keys={list(data)[:5]}")
    return block


def _pick(row: dict, *candidates: str) -> str | None:
    """여러 후보 필드명 중 첫 번째로 존재하는 값을 반환(방어적 필드 접근)."""
    for c in candidates:
        if c in row and row[c] not in (None, ""):
            return row[c]
    return None


def _to_float(s) -> float | None:
    if s is None:
        return None
    try:
        return float(str(s).replace(",", "").replace("%", "").strip())
    except (ValueError, AttributeError):
        return None


# ---- parsers (네트워크 무관 — 단위 테스트 대상) ----

def parse_kospi_index_close(rows: list[dict]) -> float | None:
    """idx/kospi_dd_trd OutBlock_1에서 대표 KOSPI 지수 종가를 뽑는다.

    여러 지수(코스피/코스피200 등)가 섞여 오므로 IDX_NM이 '코스피'/'KOSPI'인
    행을 우선 선택, 없으면 첫 행.
    """
    if not rows:
        return None
    main = None
    for r in rows:
        nm = (_pick(r, "IDX_NM", "IDX_NM_KOR", "IDX_NM1") or "").strip()
        if nm in ("코스피", "KOSPI"):
            main = r
            break
    main = main or rows[0]
    return _to_float(_pick(main, "CLSPRC_IDX", "CLSPRC", "TDD_CLSPRC", "PRC"))


def breadth_from_stocks(rows: list[dict]) -> tuple[int, int] | None:
    """stk_bydd_trd OutBlock_1에서 상승/하락 종목 수(등락률 부호)."""
    if not rows:
        return None
    adv = dec = 0
    seen = False
    for r in rows:
        rt = _to_float(_pick(r, "FLUC_RT", "CMPPREVDD_RT", "FLUC_RATE"))
        if rt is None:
            continue
        seen = True
        if rt > 0:
            adv += 1
        elif rt < 0:
            dec += 1
    return (adv, dec) if seen else None


def total_market_cap_from_stocks(rows: list[dict]) -> float | None:
    """stk_bydd_trd OutBlock_1에서 전체 시가총액 합(KRW)."""
    if not rows:
        return None
    total = 0.0
    seen = False
    for r in rows:
        mc = _to_float(_pick(r, "MKTCAP", "MKT_CAP", "MKTCAP_KRW"))
        if mc is not None:
            total += mc
            seen = True
    return total if seen else None


# ---- single-day fetchers (OpenAPI 1차 소스; 실패 시 호출측이 폴백) ----

def _recent_bas_dd(max_back: int = 7) -> list[str]:
    """오늘부터 거슬러 올라가며 영업일 후보 YYYYMMDD 리스트(주말/공휴일 회피용)."""
    today = date.today()
    return [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(max_back)]


def fetch_kospi_level() -> tuple[float, date] | None:
    """대표 KOSPI 지수 종가(가장 최근 영업일). 실패/무키 시 None."""
    if not is_enabled():
        return None
    for bd in _recent_bas_dd():
        try:
            rows = _get(EP_KOSPI_INDEX, bd)
        except KrxAuthError:
            return None
        except Exception:
            continue
        close = parse_kospi_index_close(rows)
        if close is not None:
            return close, date(int(bd[:4]), int(bd[4:6]), int(bd[6:8]))
    return None


def fetch_breadth() -> tuple[int, int, date] | None:
    """KOSPI 상승/하락 종목 수(가장 최근 영업일). 실패/무키 시 None."""
    if not is_enabled():
        return None
    for bd in _recent_bas_dd():
        try:
            rows = _get(EP_KOSPI_STOCKS, bd)
        except KrxAuthError:
            return None
        except Exception:
            continue
        b = breadth_from_stocks(rows)
        if b is not None:
            return b[0], b[1], date(int(bd[:4]), int(bd[4:6]), int(bd[6:8]))
    return None


def fetch_total_market_cap() -> tuple[float, date] | None:
    """KOSPI 전체 시가총액 합(가장 최근 영업일). 실패/무키 시 None."""
    if not is_enabled():
        return None
    for bd in _recent_bas_dd():
        try:
            rows = _get(EP_KOSPI_STOCKS, bd)
        except KrxAuthError:
            return None
        except Exception:
            continue
        mc = total_market_cap_from_stocks(rows)
        if mc is not None:
            return mc, date(int(bd[:4]), int(bd[4:6]), int(bd[6:8]))
    return None


def verify_krx_openapi() -> dict:
    """네트워크 가능한 환경에서 1회 실호출 검증용. 각 엔드포인트 결과/오류를 요약.

    사용: `python -c "import config_loader, json; from data import krx_openapi;
    print(json.dumps(krx_openapi.verify_krx_openapi(), ensure_ascii=False, indent=2))"`
    """
    out: dict = {"enabled": is_enabled()}
    if not is_enabled():
        out["error"] = "KRX_API_KEY 미설정(.env)"
        return out
    bd = _recent_bas_dd()[1]  # 어제(주말이면 빈 응답일 수 있음)
    for label, path in (("index", EP_KOSPI_INDEX), ("stocks", EP_KOSPI_STOCKS)):
        try:
            rows = _get(path, bd)
            out[label] = {"ok": True, "basDd": bd, "n_rows": len(rows),
                          "sample_keys": sorted(rows[0].keys())[:20] if rows else []}
        except Exception as e:
            out[label] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return out
