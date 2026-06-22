from datetime import date, timedelta

import pandas as pd
import yfinance as yf
from pykrx import stock

from data import krx_openapi

KOSPI_INDEX_TICKER = "1001"
KOSPI_YF_TICKER = "^KS11"


def _date_range(days=10):
    today = date.today()
    return (today - timedelta(days=days)).strftime("%Y%m%d"), today.strftime("%Y%m%d")


def _fetch_from_pykrx():
    fromdate, todate = _date_range()
    df = stock.get_index_ohlcv(fromdate, todate, KOSPI_INDEX_TICKER)
    if df is None or df.empty:
        raise ValueError("empty response (KRX_ID/KRX_PW 인증이 필요할 수 있음)")
    last = df.iloc[-1]
    return float(last["종가"]), df.index[-1].date()


def _fetch_from_yfinance():
    hist = yf.Ticker(KOSPI_YF_TICKER).history(period="10d")
    if hist.empty:
        raise ValueError("empty response")
    last = hist.iloc[-1]
    return float(last["Close"]), hist.index[-1].date()


def fetch_kospi_level():
    """Returns (value, as_of_date, source, error). value is None only if all sources fail.
    Source priority: KRX OpenAPI (AUTH_KEY) -> pykrx -> Yahoo Finance."""
    oa = krx_openapi.fetch_kospi_level()  # None if no key / unavailable
    if oa is not None:
        return oa[0], oa[1], "KRX OpenAPI", None
    try:
        value, as_of = _fetch_from_pykrx()
        return value, as_of, "KRX", None
    except Exception as krx_error:
        try:
            value, as_of = _fetch_from_yfinance()
            return value, as_of, "Yahoo Finance", None
        except Exception as yf_error:
            return None, None, None, f"KRX: {krx_error} / Yahoo: {yf_error}"


def fetch_kospi_level_series(lookback_days=365):
    """Returns (series, source, error). series is the daily close, indexed by date."""
    try:
        fromdate, todate = _date_range(lookback_days)
        df = stock.get_index_ohlcv(fromdate, todate, KOSPI_INDEX_TICKER)
        if df is None or df.empty:
            raise ValueError("empty response (KRX_ID/KRX_PW 인증이 필요할 수 있음)")
        return df["종가"], "KRX", None
    except Exception as krx_error:
        try:
            hist = yf.Ticker(KOSPI_YF_TICKER).history(period=f"{lookback_days}d")
            if hist.empty:
                raise ValueError("empty response")
            return hist["Close"], "Yahoo Finance", None
        except Exception as yf_error:
            return None, None, f"KRX: {krx_error} / Yahoo: {yf_error}"


def fetch_foreign_institutional_netbuy(lookback_days=20):
    """Daily KOSPI net-buy by investor type (KRW). Returns (df, error); df has
    columns 기관합계/기타법인/개인/외국인합계/전체, indexed by date. Requires
    KRX_ID/KRX_PW for a real (non-empty) response."""
    try:
        fromdate, todate = _date_range(lookback_days)
        df = stock.get_market_trading_value_by_date(fromdate, todate, "KOSPI", on="순매수")
        if df is None or df.empty:
            raise ValueError("empty response (KRX_ID/KRX_PW 인증 필요)")
        return df, None
    except Exception as e:
        return None, str(e)


def fetch_breadth(target_date=None):
    """Single-day KOSPI advancers/decliners. Returns (advancers, decliners, as_of, error).
    Source priority: KRX OpenAPI -> pykrx."""
    if target_date is None:
        oa = krx_openapi.fetch_breadth()  # None if no key / unavailable
        if oa is not None:
            return oa[0], oa[1], oa[2], None
    try:
        d = target_date or date.today()
        df = stock.get_market_ohlcv_by_ticker(d.strftime("%Y%m%d"), market="KOSPI", alternative=True)
        if df is None or df.empty:
            raise ValueError("empty response (KRX_ID/KRX_PW 인증 필요)")
        advancers = int((df["등락률"] > 0).sum())
        decliners = int((df["등락률"] < 0).sum())
        return advancers, decliners, d, None
    except Exception as e:
        return None, None, None, str(e)


def fetch_kospi_fundamental():
    """Returns (trailing_per, forward_per, as_of_date, error). Requires KRX auth; no free
    fallback exists (yfinance does not carry PER for index-level tickers). forward_per
    (KRX's own '선행PER' column) is unreliable — KRX often reports it as 0.0 when no
    consensus estimate is on file, so treat it only as an opportunistic cross-check
    against manual_overrides forward EPS, never as the primary source."""
    try:
        fromdate, todate = _date_range()
        df = stock.get_index_fundamental(fromdate, todate, KOSPI_INDEX_TICKER)
        if df is None or df.empty:
            raise ValueError("empty response (KRX_ID/KRX_PW 인증 필요)")
        last = df.iloc[-1]
        forward_per = float(last["선행PER"]) if last.get("선행PER") else None
        return float(last["PER"]), forward_per, df.index[-1].date(), None
    except Exception as e:
        return None, None, None, str(e)


def fetch_kospi_total_market_cap():
    """Sums per-ticker market cap across all KOSPI tickers for today. Returns (value_krw, as_of_date, error).
    Source priority: KRX OpenAPI -> pykrx."""
    oa = krx_openapi.fetch_total_market_cap()  # None if no key / unavailable
    if oa is not None:
        return oa[0], oa[1], None
    try:
        d = date.today()
        df = stock.get_market_cap_by_ticker(d.strftime("%Y%m%d"), market="KOSPI", alternative=True)
        if df is None or df.empty:
            raise ValueError("empty response (KRX_ID/KRX_PW 인증 필요)")
        return float(df["시가총액"].sum()), d, None
    except Exception as e:
        return None, None, str(e)


def fetch_breadth_series(lookback_days=10, max_calendar_days=30):
    """Walks back day-by-day collecting one snapshot per trading day. Returns (df, error);
    df has columns advancers/decliners indexed by date."""
    try:
        rows = {}
        cursor = date.today()
        scanned = 0
        while len(rows) < lookback_days and scanned < max_calendar_days:
            try:
                df = stock.get_market_ohlcv_by_ticker(cursor.strftime("%Y%m%d"), market="KOSPI")
                if df is not None and not df.empty and not (df["등락률"] == 0).all():
                    rows[cursor] = {
                        "advancers": int((df["등락률"] > 0).sum()),
                        "decliners": int((df["등락률"] < 0).sum()),
                    }
            except Exception:
                pass
            cursor -= timedelta(days=1)
            scanned += 1
        if not rows:
            raise ValueError("empty response (KRX_ID/KRX_PW 인증 필요)")
        return pd.DataFrame.from_dict(rows, orient="index").sort_index(), None
    except Exception as e:
        return None, str(e)
