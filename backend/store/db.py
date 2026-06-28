"""SQLite read-through cache for the dashboard.

Implements the schema from planning/데이터저장구조.md §2 (PoC subset: 3 tables).
All time-series (FRED, index levels, individual tickers, sector ETFs) live in one
long-format table keyed by (series_id, date). Scores and sector metrics accrue daily
so history survives restarts — which is what RRG tails and v3 walk-forward need.
"""
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "dashboard.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS series_daily (
    series_id   TEXT NOT NULL,
    date        TEXT NOT NULL,
    value       REAL NOT NULL,
    source      TEXT NOT NULL,
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (series_id, date)
);
CREATE INDEX IF NOT EXISTS idx_series_daily_lookup ON series_daily(series_id, date);

CREATE TABLE IF NOT EXISTS series_ohlc_daily (
    series_id        TEXT NOT NULL,
    date             TEXT NOT NULL,
    open             REAL,
    high             REAL,
    low              REAL,
    close            REAL,
    volume           REAL,
    source           TEXT NOT NULL,
    open_fetched_at  TEXT,
    close_fetched_at TEXT,
    fetched_at       TEXT NOT NULL,
    PRIMARY KEY (series_id, date)
);
CREATE INDEX IF NOT EXISTS idx_series_ohlc_lookup ON series_ohlc_daily(series_id, date);

CREATE TABLE IF NOT EXISTS scores_daily (
    market      TEXT NOT NULL,
    date        TEXT NOT NULL,
    s01 REAL, s02 REAL, s03 REAL, s04 REAL, s05 REAL, s06 REAL,
    composite   REAL,
    regime      TEXT,
    n_available INTEGER,
    PRIMARY KEY (market, date)
);

CREATE TABLE IF NOT EXISTS sector_metrics_daily (
    market       TEXT NOT NULL,
    sector_code  TEXT NOT NULL,
    date         TEXT NOT NULL,
    market_cap   REAL,
    ytd_pct      REAL,
    rs_ratio     REAL,
    rs_momentum  REAL,
    quadrant     TEXT,
    PRIMARY KEY (market, sector_code, date)
);
CREATE INDEX IF NOT EXISTS idx_sector_metrics_trail ON sector_metrics_daily(market, sector_code, date);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")  # tolerate concurrent reads during a write
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(_SCHEMA)


# ---- series_daily ----

def query_latest_date(series_id):
    """Most recent stored date for a series, or None. Returns a date object."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM series_daily WHERE series_id = ?", (series_id,)
        ).fetchone()
    if not row or row[0] is None:
        return None
    return date.fromisoformat(row[0])


def query_latest_fetched_at(series_id):
    """Most recent fetched_at (ISO string) for a series, or None. Used by the
    read-through to skip same-day re-fetches: daily-close data won't change if we
    already pulled it today, so latest_date lagging today() (weekend/after-close)
    must NOT force a re-fetch every request."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(fetched_at) FROM series_daily WHERE series_id = ?", (series_id,)
        ).fetchone()
    if not row or row[0] is None:
        return None
    return row[0]


def upsert_series(series_id, points, source, fetched_at):
    """points: iterable of (date_obj_or_iso, value). Idempotent on (series_id, date)."""
    rows = []
    for d, v in points:
        if v is None:
            continue
        d_iso = d.isoformat() if hasattr(d, "isoformat") else str(d)
        rows.append((series_id, d_iso, float(v), source, fetched_at))
    if not rows:
        return 0
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO series_daily (series_id, date, value, source, fetched_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(series_id, date) DO UPDATE SET "
            "value=excluded.value, source=excluded.source, fetched_at=excluded.fetched_at",
            rows,
        )
    return len(rows)


def read_series(series_id, lookback_days=None):
    """Returns list of (date_obj, value) ascending. lookback_days trims to the most recent N rows."""
    sql = "SELECT date, value FROM series_daily WHERE series_id = ? ORDER BY date ASC"
    with get_connection() as conn:
        rows = conn.execute(sql, (series_id,)).fetchall()
    out = [(date.fromisoformat(d), v) for d, v in rows]
    if lookback_days and len(out) > lookback_days:
        out = out[-lookback_days:]
    return out


# ---- series_ohlc_daily ----

def _to_float_or_none(value):
    if value is None:
        return None
    try:
        result = float(value)
        return None if result != result else result
    except (TypeError, ValueError):
        return None


def upsert_ohlc_series(series_id, points, source, fetched_at, phase=None):
    """Persist OHLC rows without letting an open capture overwrite close fields.

    phase:
      - "open": update only the open column/open_fetched_at.
      - "close": update close/high/low/volume, and fill open if present.
      - None: historical/snapshot load; update all OHLC fields.
    """
    rows = []
    phase = phase if phase in ("open", "close") else None
    for point in points:
        if isinstance(point, dict):
            d = point.get("date")
            open_v = point.get("open")
            high_v = point.get("high")
            low_v = point.get("low")
            close_v = point.get("close")
            volume_v = point.get("volume")
        else:
            d, open_v, high_v, low_v, close_v, volume_v = point
        if d is None:
            continue

        if phase == "open":
            high_v = low_v = close_v = volume_v = None
            open_fetched_at = fetched_at
            close_fetched_at = None
        elif phase == "close":
            open_fetched_at = None
            close_fetched_at = fetched_at
        else:
            open_fetched_at = fetched_at
            close_fetched_at = fetched_at

        if all(v is None for v in (open_v, high_v, low_v, close_v, volume_v)):
            continue
        d_iso = d.isoformat() if hasattr(d, "isoformat") else str(d)
        rows.append((
            series_id,
            d_iso,
            _to_float_or_none(open_v),
            _to_float_or_none(high_v),
            _to_float_or_none(low_v),
            _to_float_or_none(close_v),
            _to_float_or_none(volume_v),
            source,
            open_fetched_at,
            close_fetched_at,
            fetched_at,
        ))
    if not rows:
        return 0
    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO series_ohlc_daily "
            "(series_id, date, open, high, low, close, volume, source, "
            "open_fetched_at, close_fetched_at, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(series_id, date) DO UPDATE SET "
            "open=COALESCE(series_ohlc_daily.open, excluded.open), "
            "high=COALESCE(excluded.high, series_ohlc_daily.high), "
            "low=COALESCE(excluded.low, series_ohlc_daily.low), "
            "close=COALESCE(excluded.close, series_ohlc_daily.close), "
            "volume=COALESCE(excluded.volume, series_ohlc_daily.volume), "
            "source=excluded.source, "
            "open_fetched_at=COALESCE(series_ohlc_daily.open_fetched_at, excluded.open_fetched_at), "
            "close_fetched_at=COALESCE(excluded.close_fetched_at, series_ohlc_daily.close_fetched_at), "
            "fetched_at=excluded.fetched_at",
            rows,
        )
    return len(rows)


def read_ohlc_series(series_id, lookback_days=None):
    sql = (
        "SELECT date, open, high, low, close, volume, source, open_fetched_at, "
        "close_fetched_at, fetched_at FROM series_ohlc_daily "
        "WHERE series_id = ? ORDER BY date ASC"
    )
    with get_connection() as conn:
        rows = conn.execute(sql, (series_id,)).fetchall()
    if lookback_days and len(rows) > lookback_days:
        rows = rows[-lookback_days:]
    return [
        {
            "date": d,
            "open": open_v,
            "high": high_v,
            "low": low_v,
            "close": close_v,
            "volume": volume_v,
            "source": source,
            "open_fetched_at": open_fetched_at,
            "close_fetched_at": close_fetched_at,
            "fetched_at": fetched_at,
        }
        for d, open_v, high_v, low_v, close_v, volume_v, source, open_fetched_at, close_fetched_at, fetched_at in rows
    ]


# ---- scores_daily ----

def upsert_scores(market, d, subscores, composite, regime, n_available):
    d_iso = d.isoformat() if hasattr(d, "isoformat") else str(d)
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO scores_daily (market, date, s01, s02, s03, s04, s05, s06, "
            "composite, regime, n_available) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(market, date) DO UPDATE SET "
            "s01=excluded.s01, s02=excluded.s02, s03=excluded.s03, s04=excluded.s04, "
            "s05=excluded.s05, s06=excluded.s06, composite=excluded.composite, "
            "regime=excluded.regime, n_available=excluded.n_available",
            (market, d_iso, subscores.get("S01"), subscores.get("S02"), subscores.get("S03"),
             subscores.get("S04"), subscores.get("S05"), subscores.get("S06"),
             composite, regime, n_available),
        )


# ---- sector_metrics_daily ----

def upsert_sector_metric(market, sector_code, d, market_cap, ytd_pct, rs_ratio, rs_momentum, quadrant):
    d_iso = d.isoformat() if hasattr(d, "isoformat") else str(d)
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sector_metrics_daily (market, sector_code, date, market_cap, "
            "ytd_pct, rs_ratio, rs_momentum, quadrant) VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(market, sector_code, date) DO UPDATE SET "
            "market_cap=excluded.market_cap, ytd_pct=excluded.ytd_pct, "
            "rs_ratio=excluded.rs_ratio, rs_momentum=excluded.rs_momentum, quadrant=excluded.quadrant",
            (market, sector_code, d_iso, market_cap, ytd_pct, rs_ratio, rs_momentum, quadrant),
        )


def read_sector_tail(market, sector_code, lookback_days=20):
    sql = ("SELECT date, rs_ratio, rs_momentum FROM sector_metrics_daily "
           "WHERE market = ? AND sector_code = ? ORDER BY date ASC")
    with get_connection() as conn:
        rows = conn.execute(sql, (market, sector_code)).fetchall()
    if lookback_days and len(rows) > lookback_days:
        rows = rows[-lookback_days:]
    return [{"date": d, "rsRatio": r, "rsMomentum": m} for d, r, m in rows]
