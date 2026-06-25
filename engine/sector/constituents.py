"""engine/sector/constituents.py — 섹터별 주도주(구성종목) 목록.

기존 큐레이션 주도주(sectors.json key/star)는 2섹터만 채워져 있어 대부분 섹터가
"주도주 데이터 없음"으로 비었다. 이 모듈은 **모든** 섹터에 7개 안팎의 주도주를
채운다(비동결 /api/sectors envelope에 가산 — 동결 payload·등가성 게이트 무관).

소스(둘 다 정적 리스트 + 런타임 메트릭):
- NASDAQ: 섹터 ETF(XLK 등) 상위 보유종목. yfinance가 CI(데이터센터 IP)에서
  throttle되므로 보유목록 자체는 정적 스냅샷(nasdaq_sector_holdings.json, 로컬에서
  갱신·커밋)으로 고정 — 비중(weight) 순. CI 네트워크 의존 없음.
- KOSPI: 내가 작성한 ticker→섹터 매핑(kospi_sector_map.json). 섹터 내 선정은
  **시총 + 거래대금 증가폭**(거래대금 surge) — KRX OpenAPI stk_bydd_trd 최근치로
  런타임 랭킹. KRX 무키/실패 시 매핑 순서(시총순으로 작성됨)로 폴백.

절대 raise하지 않는다(파일 부재·네트워크 실패 → 빈 dict/폴백).
"""
from __future__ import annotations

import json
import os
from datetime import date

from data import krx_openapi

_DIR = os.path.dirname(os.path.abspath(__file__))
_KOSPI_MAP: dict | None = None
_NASDAQ_HOLD: dict | None = None
# 한 프로세스(=한 생성 실행) 내 KRX 최근치 1회만 fetch.
_kospi_metrics_cache: dict[str, dict] = {}


def _load() -> None:
    global _KOSPI_MAP, _NASDAQ_HOLD
    if _KOSPI_MAP is None:
        try:
            with open(os.path.join(_DIR, "kospi_sector_map.json"), encoding="utf-8") as f:
                _KOSPI_MAP = json.load(f)
        except Exception:
            _KOSPI_MAP = {}
    if _NASDAQ_HOLD is None:
        try:
            with open(os.path.join(_DIR, "nasdaq_sector_holdings.json"), encoding="utf-8") as f:
                _NASDAQ_HOLD = json.load(f)
        except Exception:
            _NASDAQ_HOLD = {}


def _kospi_krx_metrics() -> dict[str, dict]:
    """{code: {mktcap, trdval, surge}} — 최근 영업일 시총/거래대금 + 거래대금 증가폭.

    surge = 최근일 거래대금 / 직전 5영업일 평균 거래대금. KRX 무키/실패 시 빈 dict.
    """
    day = date.today().isoformat()
    if day in _kospi_metrics_cache:
        return _kospi_metrics_cache[day]

    metrics: dict[str, dict] = {}
    if krx_openapi.is_enabled():
        per_day: list[dict[str, float]] = []  # 최근→과거 순, 각 {code: trdval}
        latest_mktcap: dict[str, float] = {}
        for bd in krx_openapi._recent_bas_dd(8):
            try:
                rows = krx_openapi._get("/sto/stk_bydd_trd", bd)
            except krx_openapi.KrxAuthError:
                break
            except Exception:
                continue
            day_map: dict[str, float] = {}
            for r in rows:
                code = (r.get("ISU_CD") or "").strip()
                tv = krx_openapi._to_float(r.get("ACC_TRDVAL"))
                mc = krx_openapi._to_float(r.get("MKTCAP"))
                if code and tv is not None:
                    day_map[code] = tv
                if code and mc is not None and not per_day:  # 첫(최근) 영업일 시총
                    latest_mktcap[code] = mc
            if day_map:
                per_day.append(day_map)
        if per_day:
            today_map = per_day[0]
            prior = per_day[1:6]
            for code, mc in latest_mktcap.items():
                tv_today = today_map.get(code)
                prior_vals = [d[code] for d in prior if d.get(code)]
                avg_prior = sum(prior_vals) / len(prior_vals) if prior_vals else None
                surge = (tv_today / avg_prior) if (tv_today and avg_prior and avg_prior > 0) else None
                metrics[code] = {"mktcap": mc, "trdval": tv_today, "surge": surge}

    _kospi_metrics_cache[day] = metrics
    return metrics


def _kospi_note(s: dict) -> str:
    parts = []
    if s.get("mktcap"):
        parts.append(f"시총 {s['mktcap'] / 1e12:.0f}조")
    if s.get("surge"):
        parts.append(f"거래대금 {(s['surge'] - 1) * 100:+.0f}%")
    return " · ".join(parts)


def _rank_kospi(scored: list[dict]) -> list[dict]:
    """섹터 내 시총·거래대금증가폭 정규화 합성점수 내림차순. KRX 메트릭 부재 시
    작성된 매핑 순서(시총순)를 그대로 둔다."""
    mcs = [s["mktcap"] for s in scored if s.get("mktcap")]
    if not mcs:
        return scored  # KRX 실패 → 매핑 순서 유지
    mc_max = max(mcs)
    sgs = [s["surge"] for s in scored if s.get("surge")]
    sg_max = max(sgs) if sgs else 1.0

    def score(s: dict) -> float:
        mc = (s["mktcap"] / mc_max) if (s.get("mktcap") and mc_max) else 0.0
        sg = (s["surge"] / sg_max) if (s.get("surge") and sg_max) else 0.0
        return 0.6 * mc + 0.4 * sg

    return sorted(scored, key=score, reverse=True)


def get_constituents_for_market(market: str, top_n: int = 7) -> dict[str, list[dict]]:
    """{sector_code: [{ticker, name, note, source}]} — 섹터별 상위 top_n 주도주."""
    _load()
    out: dict[str, list[dict]] = {}

    if market == "NASDAQ":
        for code, d in (_NASDAQ_HOLD or {}).items():
            out[code] = [
                {
                    "ticker": h["ticker"],
                    "name": h["name"],
                    "note": f"비중 {h['weight'] * 100:.1f}%" if h.get("weight") else "",
                    "source": "etf",
                }
                for h in d.get("holdings", [])[:top_n]
            ]
        return out

    # KOSPI
    metrics = _kospi_krx_metrics()
    for sect, items in (_KOSPI_MAP or {}).items():
        scored = [
            {
                "ticker": it["ticker"],
                "name": it["name"],
                **{k: metrics.get(it["ticker"], {}).get(k) for k in ("mktcap", "trdval", "surge")},
            }
            for it in items
        ]
        ranked = _rank_kospi(scored)[:top_n]
        out[sect] = [
            {"ticker": s["ticker"], "name": s["name"], "note": _kospi_note(s), "source": "krx"}
            for s in ranked
        ]
    return out
