"""GET /api/history/{market} — sector RRG trail endpoint (Phase A, §history).

신규 비동결 엔드포인트. 프론트의 RRG trail 오버레이(섹터 클릭 시 과거 경로)가 이걸
소비한다. `db.read_sector_tail`(읽기 전용, backend/store/db.py 무수정)로 일별
(date, rsRatio, rsMomentum)을 가져와 tf 번들로 리샘플한다 — sector_metrics_daily는
항상 1D로만 upsert되므로(engine/sector/inputs.py 가드) 여기 저장된 시계열은 늘
일별이고, 이 엔드포인트가 그걸 tf에 맞게 다시 리샘플하는 쪽이다.

tf="1D"는 원본 tail을 그대로(리샘플 없이) 반환한다 — identity, 새 엔드포인트라
byte-identical 게이트 대상은 아니지만 동일한 원칙(불필요한 변환 금지)을 따른다.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.store import db
from config_loader import load_sectors
from engine.core.timeframes import normalize_tf, resample_for_tf

router = APIRouter()

VALID_MARKETS = ("KOSPI", "NASDAQ")

# Tail lookback: 1.6y of daily history at most — generous enough that even 1Y
# resampling has multiple points once more history accumulates.
LOOKBACK_DAYS = 600


def _trail_to_series(trail, field):
    """trail(list of {"date","rsRatio","rsMomentum"}) -> pandas Series for `field`,
    indexed by Timestamp, dropping rows where the field is None."""
    import pandas as pd

    pairs = [(row["date"], row[field]) for row in trail if row[field] is not None]
    if not pairs:
        return None
    s = pd.Series({d: v for d, v in pairs})
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def _resample_trail(trail, tf):
    """Resample a raw daily trail (list of {"date","rsRatio","rsMomentum"}) to tf.

    tf="1D" returns the trail unchanged (identity). For other tf, rsRatio and
    rsMomentum are each resampled independently via resample_for_tf (last-of-period),
    then re-joined by date."""
    if tf == "1D" or not trail:
        return trail

    ratio_series = _trail_to_series(trail, "rsRatio")
    momentum_series = _trail_to_series(trail, "rsMomentum")
    ratio_rs = resample_for_tf(ratio_series, tf)
    momentum_rs = resample_for_tf(momentum_series, tf)

    dates = set()
    if ratio_rs is not None:
        dates.update(ratio_rs.index)
    if momentum_rs is not None:
        dates.update(momentum_rs.index)

    out = []
    for d in sorted(dates):
        out.append({
            "date": d.date().isoformat(),
            "rsRatio": float(ratio_rs.loc[d]) if ratio_rs is not None and d in ratio_rs.index else None,
            "rsMomentum": float(momentum_rs.loc[d]) if momentum_rs is not None and d in momentum_rs.index else None,
        })
    return out


def _trail_dates_to_str(trail):
    """raw db.read_sector_tail() rows carry date objects -- stringify for JSON/identity passthrough."""
    return [
        {
            "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"]),
            "rsRatio": row["rsRatio"],
            "rsMomentum": row["rsMomentum"],
        }
        for row in trail
    ]


@router.get("/api/history/{market}")
def get_history(market: str, tf: str = "1D"):
    market = market.upper()
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=404, detail=f"unknown market: {market}")
    tf = normalize_tf(tf)
    try:
        sectors_config = load_sectors()
        sector_defs = sectors_config[market]["sectors"]
        sectors_out = []
        for code in sector_defs:
            raw_trail = db.read_sector_tail(market, code, lookback_days=LOOKBACK_DAYS)
            raw_trail = _trail_dates_to_str(raw_trail)
            trail = _resample_trail(raw_trail, tf)
            sectors_out.append({"code": code, "trail": trail})
    except Exception as exc:  # never 500 — graceful degradation(§9.3)
        raise HTTPException(status_code=503, detail=f"history assembly failed: {exc}")
    return {
        "tier": "history",
        "market": market,
        "tf": tf,
        "sectors": sectors_out,
    }
