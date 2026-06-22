"""GET /api/history/{market} — sector RRG trail + snapshot score-trend endpoint.

신규 비동결 엔드포인트. 프론트의 RRG trail 오버레이(섹터 클릭 시 과거 경로)가 이걸
소비한다. `db.read_sector_tail`(읽기 전용, backend/store/db.py 무수정)로 일별
(date, rsRatio, rsMomentum)을 가져와 tf 번들로 리샘플한다 — sector_metrics_daily는
항상 1D로만 upsert되므로(engine/sector/inputs.py 가드) 여기 저장된 시계열은 늘
일별이고, 이 엔드포인트가 그걸 tf에 맞게 다시 리샘플하는 쪽이다.

tf="1D"는 원본 tail을 그대로(리샘플 없이) 반환한다 — identity, 새 엔드포인트라
byte-identical 게이트 대상은 아니지만 동일한 원칙(불필요한 변환 금지)을 따른다.

Phase B (§history 확장): 스냅샷 지표(Regime composite, S01~S06 헤드룸, F&G)는
헤드라인 값은 "현재"를 유지하되, tf 구간의 **점수-추세**를 추가로 노출한다(가짜
재계산이 아니라 "그 기간 동안 개선/악화"를 보여주는 스파크라인 데이터).
- `scores`: scores_daily(날짜별 S01~S06+composite, db.get_connection()로 SELECT만,
  db.py 무수정)를 tf로 리샘플.
- `fearGreed`: F&G는 scores_daily에 저장되지 않으므로(라이브 전용 계산) 저장된
  입력 시리즈(index level, fred:vix, fred:hy_oas)로부터 scoring_ext.fear_greed()를
  재계산해 추세를 만든다 — best-effort, 입력 부족 시 그 지점/전체를 건너뛴다.
"""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException

from backend import scoring_ext
from backend.store import db, series_map
from config_loader import load_config, load_sectors
from engine.core.timeframes import normalize_tf, resample_for_tf

router = APIRouter()

VALID_MARKETS = ("KOSPI", "NASDAQ")

# Tail lookback: 1.6y of daily history at most — generous enough that even 1Y
# resampling has multiple points once more history accumulates.
LOOKBACK_DAYS = 600

SCORE_FIELDS = ("s01", "s02", "s03", "s04", "s05", "s06", "composite")


def _trail_to_series(trail, field):
    """trail(list of {"date","rsRatio","rsMomentum"}) -> pandas Series for `field`,
    indexed by Timestamp, dropping rows where the field is None."""
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


def _read_scores_daily(market):
    """SELECT date, s01..s06, composite FROM scores_daily — read-only via the
    existing public db.get_connection() (db.py itself is not modified; no new
    function added there per the guardrail). Returns list of sqlite3 rows
    (tuples) ordered by date ASC, or [] on any failure."""
    sql = (
        "SELECT date, s01, s02, s03, s04, s05, s06, composite "
        "FROM scores_daily WHERE market = ? ORDER BY date ASC"
    )
    try:
        with db.get_connection() as conn:
            return conn.execute(sql, (market,)).fetchall()
    except Exception:
        return []


def _series_to_points(series):
    """pandas Series (DatetimeIndex -> value) -> [{"date","value"}], NaN dropped,
    sorted ascending by date. None/empty series -> []."""
    if series is None:
        return []
    clean = series.dropna()
    return [{"date": idx.date().isoformat(), "value": float(val)} for idx, val in clean.items()]


def _build_score_trends(market, tf):
    """scores_daily -> {field: [{date,value}]} resampled to tf. Each metric column
    becomes its own pandas Series (index=date) so a metric with sparse/no data
    degrades independently (empty list) rather than dragging the others down."""
    rows = _read_scores_daily(market)
    trends = {field: [] for field in SCORE_FIELDS}
    if not rows:
        return trends

    dates = [r[0] for r in rows]
    idx = pd.to_datetime(dates)
    for col_i, field in enumerate(SCORE_FIELDS, start=1):
        values = [r[col_i] for r in rows]
        s = pd.Series(values, index=idx, dtype="float64")
        s = s.dropna()
        if s.empty:
            continue
        s = s.sort_index()
        resampled = resample_for_tf(s, tf)
        trends[field] = _series_to_points(resampled)
    return trends


def _series_from_db(series_id, lookback_days):
    """db.read_series(series_id) -> pandas Series indexed by Timestamp, or None if
    no rows. Read-only reuse of the existing public db.read_series (db.py
    untouched)."""
    rows = db.read_series(series_id, lookback_days=lookback_days)
    if not rows:
        return None
    idx = pd.to_datetime([d for d, _ in rows])
    vals = [v for _, v in rows]
    return pd.Series(vals, index=idx, dtype="float64").sort_index()


def _build_fear_greed_trend(market, tf):
    """Best-effort F&G score trend, reconstructed from stored daily input series
    rather than scores_daily (F&G is not persisted there — it's computed live-only
    in gather_macro_inputs). Mirrors the live §13-1 inputs as closely as the stored
    series allow:
      - price = index level (series_map.index_series_id(market))
      - sma_125 = trailing 125-day mean of the level series (matches
        engine/macro/inputs.py's `level_series.iloc[-125:].mean()`, generalized to
        a rolling window so every date in the trail gets its own SMA)
      - up_ratio = None always — breadth (KOSPI advancers/decliners, NASDAQ
        sector up/down counts) is never persisted to series_daily/scores_daily,
        so F2 degrades exactly like the live KOSPI-without-KRX-auth path
        (fear_greed() renormalizes over the remaining factors).
      - vix_or_vkospi: NASDAQ uses fred:vix directly (matches live `vix_value`).
        KOSPI uses realized volatility of the level series (matches live
        `scoring.realized_volatility(level_series, window=20)` — recomputed here
        via pct_change/rolling std since scoring.py is protected/call-only and
        this needs a date-indexed series, not a single scalar).
      - hy_oas = fred:hy_oas.

    Simplification: rather than reimplement a rolling realized_volatility call
    per-date for KOSPI (loop), we vectorize it once over the whole level series
    with pandas .rolling(), then index into it per resampled date — equivalent
    math to scoring.realized_volatility(window=20), just computed for every date
    at once instead of one trailing window. We then loop over the (few) resampled
    dates only and call scoring_ext.fear_greed() per date, as the plan suggests.
    Any date missing a required input is skipped (not null-padded) -> shorter but
    honest trail. No data at all -> [].
    """
    config = load_config()
    fg_config = config["fear_greed"]

    level = _series_from_db(series_map.index_series_id(market), lookback_days=LOOKBACK_DAYS)
    if level is None or level.empty:
        return []

    sma_125 = level.rolling(125).mean()

    if market == "KOSPI":
        # realized_volatility(window=20): annualized stdev of trailing 20 daily
        # returns * 100 -- vectorized equivalent of scoring.realized_volatility.
        returns = level.pct_change()
        vol_input = returns.rolling(20).std() * (252 ** 0.5) * 100
    else:
        vix = _series_from_db("fred:vix", lookback_days=LOOKBACK_DAYS)
        vol_input = vix

    hy_oas = _series_from_db("fred:hy_oas", lookback_days=LOOKBACK_DAYS)

    # Resample the level index itself to get the tf's date grid, then evaluate
    # fear_greed() at each of those (few) dates -- cheap even as a per-date loop.
    resampled_level = resample_for_tf(level, tf)
    if resampled_level is None or resampled_level.empty:
        return []

    points = []
    for d in resampled_level.index:
        price = resampled_level.loc[d]
        sma_val = sma_125.loc[d] if d in sma_125.index and pd.notna(sma_125.loc[d]) else None
        vol_val = None
        if vol_input is not None:
            # nearest available input at/before d (inputs may not share level's
            # exact calendar, e.g. FRED series with different holidays).
            asof = vol_input.loc[:d]
            if not asof.empty and pd.notna(asof.iloc[-1]):
                vol_val = float(asof.iloc[-1])
        oas_val = None
        if hy_oas is not None:
            asof = hy_oas.loc[:d]
            if not asof.empty and pd.notna(asof.iloc[-1]):
                oas_val = float(asof.iloc[-1])

        result = scoring_ext.fear_greed(
            price=float(price) if pd.notna(price) else None,
            sma_125=float(sma_val) if sma_val is not None else None,
            up_ratio=None,
            vix_or_vkospi=vol_val,
            hy_oas=oas_val,
            fg_config=fg_config,
        )
        score = result.get("score")
        if score is None:
            continue
        points.append({"date": d.date().isoformat(), "value": float(score)})
    return points


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

    try:
        scores_out = _build_score_trends(market, tf)
    except Exception:  # never 500 — score trend is best-effort, degrade to empty
        scores_out = {field: [] for field in SCORE_FIELDS}

    try:
        fear_greed_out = _build_fear_greed_trend(market, tf)
    except Exception:  # never 500 — F&G trend is best-effort, degrade to empty
        fear_greed_out = []

    return {
        "tier": "history",
        "market": market,
        "tf": tf,
        "sectors": sectors_out,
        "scores": scores_out,
        "fearGreed": fear_greed_out,
    }
