"""Read-through ingestion: check DB latest date, fetch only the gap, upsert.

Track A fills in the per-series wiring (which fetch_fn maps to which series_id).
This module provides the orchestration skeleton so the pattern is fixed in Track 0.
"""
import os
from datetime import date, datetime

from . import db


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _intraday_refresh_ttl_minutes():
    raw = os.environ.get("SERIES_INTRADAY_REFRESH_TTL_MINUTES", "180")
    try:
        return max(0, int(raw))
    except ValueError:
        return 180


def _allows_intraday_refresh(source):
    source_l = (source or "").lower()
    return "yfinance" in source_l


def _fetched_recently(fetched_at, ttl_minutes):
    try:
        fetched_dt = datetime.fromisoformat(fetched_at)
    except (TypeError, ValueError):
        return False
    now = datetime.now(fetched_dt.tzinfo) if fetched_dt.tzinfo else datetime.now()
    return (now - fetched_dt).total_seconds() < ttl_minutes * 60


def ensure_series_up_to_date(series_id, fetch_fn, source, bootstrap_lookback_days=365):
    """fetch_fn(lookback_days) -> iterable of (date, value).

    On first sight of a series, bootstraps the full lookback. Afterwards fetches only
    (today - latest + 2) days and upserts. yfinance-backed daily rows can also be
    refreshed after a short TTL because Yahoo's current-day "Close" may be an
    intraday last price before the official close settles. Returns number of rows
    written.
    Never raises on fetch failure — logs to the caller via return of 0 and re-raises
    only programming errors; data-source failures should be swallowed by fetch_fn
    (matching the existing data/*.py graceful-degradation contract).
    """
    latest = db.query_latest_date(series_id)
    if latest is None:
        lookback = bootstrap_lookback_days
    else:
        # Same-day short-circuit: if we already pulled this series today, don't re-fetch.
        # Daily-close data won't change intraday, and on weekends/after-close latest (last
        # trading day) is always < today() — without this guard the gap check below would
        # re-fetch on EVERY request, defeating the cache (warm reloads stayed ~24s).
        fetched_at = db.query_latest_fetched_at(series_id)
        intraday_refresh = _allows_intraday_refresh(source)
        if fetched_at and fetched_at[:10] == date.today().isoformat():
            if not intraday_refresh:
                return 0
            if _fetched_recently(fetched_at, _intraday_refresh_ttl_minutes()):
                return 0
        gap = (date.today() - latest).days
        if gap <= 0:
            if not intraday_refresh:
                return 0  # already current
            lookback = 2
        else:
            lookback = gap + 2
    points = fetch_fn(lookback)
    if not points:
        return 0
    return db.upsert_series(series_id, points, source=source, fetched_at=_now_iso())


def refresh_ohlc_series(series_id, fetch_fn, source, lookback_days=5, phase=None):
    """Fetch recent OHLC rows and persist them in series_ohlc_daily.

    This intentionally does not share the series_daily same-day guard: the open and
    close captures are separate events for the same market date.
    """
    points = fetch_fn(lookback_days)
    if not points:
        return 0
    return db.upsert_ohlc_series(series_id, points, source=source, fetched_at=_now_iso(), phase=phase)
