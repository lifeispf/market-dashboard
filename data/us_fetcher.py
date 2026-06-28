import yfinance as yf

TICKERS = {
    "nasdaq_composite": "^IXIC",
    "nasdaq_100": "^NDX",
    "vix": "^VIX",
}


def _clean_number(value):
    try:
        if value != value:  # NaN
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_last_price(name):
    """Returns (value, as_of_date, error). value is None on failure."""
    try:
        hist = yf.Ticker(TICKERS[name]).history(period="5d")
        if hist.empty:
            return None, None, "empty response"
        last = hist.iloc[-1]
        as_of = hist.index[-1]
        as_of = as_of.date() if hasattr(as_of, "date") else as_of
        return float(last["Close"]), as_of, None
    except Exception as e:
        return None, None, str(e)


def fetch_price_series(name, period="1y"):
    """Returns (series, error). series is the daily Close, indexed by date."""
    try:
        hist = yf.Ticker(TICKERS[name]).history(period=period)
        if hist.empty:
            return None, "empty response"
        return hist["Close"], None
    except Exception as e:
        return None, str(e)


def fetch_ohlc_series(name, period="5d"):
    """Returns (rows, error). rows contain daily OHLCV dicts indexed by market date."""
    try:
        hist = yf.Ticker(TICKERS[name]).history(period=period, interval="1d", auto_adjust=False)
        if hist.empty:
            return [], "empty response"
        rows = []
        for idx, row in hist.iterrows():
            as_of = idx.date() if hasattr(idx, "date") else idx
            rows.append({
                "date": as_of,
                "open": _clean_number(row.get("Open")),
                "high": _clean_number(row.get("High")),
                "low": _clean_number(row.get("Low")),
                "close": _clean_number(row.get("Close")),
                "volume": _clean_number(row.get("Volume")),
            })
        return rows, None
    except Exception as e:
        return [], str(e)
