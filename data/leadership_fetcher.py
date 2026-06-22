import yfinance as yf


def fetch_ticker_series(ticker, period="ytd"):
    """Returns (series, error). series is the daily Close, works for any yfinance ticker
    (US tickers, or KR tickers with .KS/.KQ suffix)."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return None, "empty response"
        return hist["Close"], None
    except Exception as e:
        return None, str(e)


def fetch_ticker_quote(ticker):
    """Returns (last_price, market_cap, error). Either value may be None if unavailable."""
    try:
        fi = yf.Ticker(ticker).fast_info
        price = fi.get("lastPrice") if hasattr(fi, "get") else getattr(fi, "last_price", None)
        market_cap = fi.get("marketCap") if hasattr(fi, "get") else getattr(fi, "market_cap", None)
        if price is None and market_cap is None:
            return None, None, "empty response"
        return price, market_cap, None
    except Exception as e:
        return None, None, str(e)


def ytd_pct(series):
    """Percent change from the first to the last point in series. None if series too short."""
    if series is None or len(series) < 2:
        return None
    first = series.iloc[0]
    if not first:
        return None
    return (series.iloc[-1] / first - 1) * 100
