"""Series-id -> fetch_fn wiring for ingest.ensure_series_up_to_date().

Track A: adapts the existing data/*.py fetchers (which return pandas Series /
DataFrames / scalars in various shapes) into the (date, value) pair iterables
that backend/store/ingest.py + db.upsert_series() expect.

Naming convention (series_id): ticker-like ids are used verbatim (e.g. "^KS11",
"NVDA", "005930.KS", "XLK") and FRED ids use the data/fred_fetcher.py logical
name (e.g. "fed_balance_sheet", "vix", "usdkrw", "hy_oas", "real_rate_2y") so a
series fetched for one purpose (e.g. S01) and reused for another (e.g. fear&greed
F3) shares one row set in series_daily instead of duplicating storage.

Every fetch_fn here returns [] (never None, never raises) on failure so
ensure_series_up_to_date()'s `if not points: return 0` short-circuits cleanly --
matching the project's graceful-degradation contract.
"""
from data import fred_fetcher, kr_fetcher, leadership_fetcher, us_fetcher

# ---- date normalization ----


def _to_date(d):
    """Coerce pandas Timestamp (tz-aware or not) / datetime / date / str -> datetime.date.

    yfinance returns tz-aware DatetimeIndex (Asia/Seoul) whose .isoformat() includes a
    UTC offset that date.fromisoformat() (used by db.read_series) cannot parse. FRED/pykrx
    series are already tz-naive. Normalizing here means db.upsert_series's own
    `d.isoformat() if hasattr(d, "isoformat") else str(d)` always gets a clean date.
    """
    if hasattr(d, "date"):
        return d.date()
    return d


def _series_to_points(series):
    """pandas Series (DatetimeIndex -> value) -> list of (date, value), NaN dropped."""
    if series is None or len(series) == 0:
        return []
    clean = series.dropna()
    return [(_to_date(idx), float(val)) for idx, val in clean.items()]


# ---- FRED-backed series (no auth needed beyond FRED_API_KEY; null gracefully without it) ----


def _fred_fetch_fn(name):
    def fetch_fn(lookback_days):
        series, _error = fred_fetcher.fetch_series(name, lookback_days=lookback_days)
        return _series_to_points(series)

    return fetch_fn


# ---- Index levels ----


# ensure_series_up_to_date()'s fetch_fn contract is `(lookback_days) -> points` with no
# secondary return channel for provenance, but kr_fetcher's KRX->yfinance fallback result
# (which actually succeeded) is useful to surface as flow.source / freshness[].source.
# Stashing it here avoids a second live re-fetch just to learn what the first one already
# determined (kr_fetcher has no separate "which source last won" query).
last_kospi_index_source = {"value": None}


def _kospi_index_fetch_fn(lookback_days):
    series, source, _error = kr_fetcher.fetch_kospi_level_series(lookback_days)
    if source is not None:
        last_kospi_index_source["value"] = source
    return _series_to_points(series)


def _nasdaq_index_fetch_fn(lookback_days):
    series, _error = us_fetcher.fetch_price_series("nasdaq_composite", period=f"{lookback_days}d")
    return _series_to_points(series)


# ---- Arbitrary tickers (sector ETFs, leader/constituent stocks) ----


def _ticker_fetch_fn(ticker):
    def fetch_fn(lookback_days):
        # leadership_fetcher takes a yfinance `period` string, not a day count; "Nd" is
        # accepted by yfinance for any N. Cap at a generous bootstrap ceiling.
        period = f"{max(lookback_days, 5)}d"
        series, _error = leadership_fetcher.fetch_ticker_series(ticker, period=period)
        return _series_to_points(series)

    return fetch_fn


# ---- Public registry ----
#
# series_id -> (fetch_fn, source_label). source_label is stored in series_daily.source
# for provenance (per 데이터저장구조.md §2).

FRED_SOURCE = "fred"
YF_SOURCE = "yfinance"
KRX_SOURCE = "krx_or_yfinance"  # kr_fetcher falls back to yfinance under the KRX auth wall


def index_series_id(market):
    return "^KS11" if market == "KOSPI" else "^IXIC"


def build_registry(market, sectors_config):
    """Returns {series_id: (fetch_fn, source_label)} for every series the given market's
    payload needs: its own index, the 6 FRED sources (shared across markets), every sector
    ETF/constituent ticker, and every key/star leader ticker."""
    registry = {}

    if market == "KOSPI":
        registry[index_series_id(market)] = (_kospi_index_fetch_fn, KRX_SOURCE)
    else:
        registry[index_series_id(market)] = (_nasdaq_index_fetch_fn, YF_SOURCE)

    # S01-S06 + F3/F4 shared raw inputs (FRED). Logical names match fred_fetcher.SERIES keys.
    for fred_name in ("fed_balance_sheet", "usdkrw", "hy_oas", "vix", "real_rate_2y"):
        registry[f"fred:{fred_name}"] = (_fred_fetch_fn(fred_name), FRED_SOURCE)

    sector_defs = sectors_config[market]["sectors"]
    tickers = set()
    for sdef in sector_defs.values():
        if "etf" in sdef:
            tickers.add(sdef["etf"])
        for tk in sdef.get("tickers", []):
            tickers.add(tk)
        for tk in sdef.get("key", []) + sdef.get("star", []):
            tickers.add(tk)

    for tk in tickers:
        registry[tk] = (_ticker_fetch_fn(tk), YF_SOURCE)

    return registry
