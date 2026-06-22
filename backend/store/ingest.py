"""Read-through ingestion: check DB latest date, fetch only the gap, upsert.

Track A fills in the per-series wiring (which fetch_fn maps to which series_id).
This module provides the orchestration skeleton so the pattern is fixed in Track 0.
"""
from datetime import date, datetime

from . import db


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def ensure_series_up_to_date(series_id, fetch_fn, source, bootstrap_lookback_days=365):
    """fetch_fn(lookback_days) -> iterable of (date, value).

    On first sight of a series, bootstraps the full lookback. Afterwards fetches only
    (today - latest + 2) days and upserts. Returns number of rows written.
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
        if fetched_at and fetched_at[:10] == date.today().isoformat():
            return 0
        gap = (date.today() - latest).days
        if gap <= 0:
            return 0  # already current
        lookback = gap + 2
    points = fetch_fn(lookback)
    if not points:
        return 0
    return db.upsert_series(series_id, points, source=source, fetched_at=_now_iso())
