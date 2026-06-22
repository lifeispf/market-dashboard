"""backend/api/_assembly_helpers.py — shared plumbing helpers for market payload assembly.

Stage 2 (Macro retrofit, planning/blueprint_unified/00_architecture.md §5/§11):
extracted verbatim out of backend/api/market.py so both the frozen regression
oracle (_reference_assembly.py) and the new engine path (engine/macro/inputs.py)
can share one definition instead of duplicating logic. No calculation changed —
this is a pure relocation.
"""
from datetime import date, datetime

import pandas as pd

from backend.store import db, ingest
from data import leadership_fetcher, manual


def _rows_to_series(rows):
    """db.read_series() rows [(date, value), ...] -> pandas Series indexed by Timestamp,
    ascending. Empty/None -> None (mirrors data/*.py's None-on-empty convention so
    downstream scoring.py calls behave exactly as they do against live fetcher output)."""
    if not rows:
        return None
    s = pd.Series({d: v for d, v in rows})
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def _cached_series(series_id, fetch_fn, source, lookback_days=400):
    """Read-through: ensure DB is current for series_id, then read lookback_days back.
    Never raises -- ingest.ensure_series_up_to_date already swallows fetch errors."""
    try:
        ingest.ensure_series_up_to_date(series_id, fetch_fn, source, bootstrap_lookback_days=max(lookback_days, 365))
    except Exception:
        pass
    rows = db.read_series(series_id, lookback_days=lookback_days)
    return _rows_to_series(rows)


def _cached_market_cap(ticker):
    """Same-day cached market cap. The per-ticker yfinance fast_info quote (~40 calls
    per market) bypasses the series read-through and was the dominant warm-reload cost
    (~12s). Stored as a one-point series 'mcap:{ticker}' so a same-day reload reads it
    from SQLite instead of re-hitting the network."""
    mcap_id = f"mcap:{ticker}"
    fetched = db.query_latest_fetched_at(mcap_id)
    if fetched and fetched[:10] == date.today().isoformat():
        rows = db.read_series(mcap_id, lookback_days=1)
        return rows[-1][1] if rows else None
    _price, cap, _err = _safe(lambda: leadership_fetcher.fetch_ticker_quote(ticker), (None, None, None))
    if cap is not None:
        db.upsert_series(
            mcap_id, [(date.today(), cap)], source="yfinance",
            fetched_at=datetime.now().isoformat(timespec="seconds"),
        )
    return cap


def _last(series):
    if series is None or len(series) == 0:
        return None
    return float(series.iloc[-1])


def _as_of_str(series):
    if series is None or len(series) == 0:
        return None
    last = series.index[-1]
    return last.date().isoformat() if hasattr(last, "date") else str(last)


def _ytd_slice(series):
    """Slice a series to this calendar year only, mirroring yfinance period='ytd'."""
    if series is None or len(series) == 0:
        return None
    start = pd.Timestamp(date(date.today().year, 1, 1))
    sliced = series[series.index >= start]
    return sliced if len(sliced) >= 2 else None


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _stale(last_str, freq, config):
    if not last_str:
        return False
    try:
        last_date = date.fromisoformat(last_str)
    except ValueError:
        return False
    return manual.staleness_level(last_date, freq, config) == "stale"
