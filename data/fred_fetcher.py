import os

import pandas as pd
from fredapi import Fred

SERIES = {
    "fed_funds_rate": "DFF",
    "fed_balance_sheet": "WALCL",
    "bank_reserves": "WRESBAL",
    "sofr": "SOFR",
    "hy_oas": "BAMLH0A0HYM2",
    "usdkrw": "DEXKOUS",
    "dollar_index": "DTWEXBGS",
    "vix": "VIXCLS",
    "ust_2y": "DGS2",
    "real_rate_2y": "DFII2",
}

_client = None
_client_error = None


def _get_client():
    global _client, _client_error
    if _client is not None or _client_error is not None:
        return _client
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        _client_error = "FRED_API_KEY 환경변수가 설정되지 않았습니다"
        return None
    try:
        _client = Fred(api_key=api_key)
    except Exception as e:
        _client_error = str(e)
    return _client


def fetch_series(name, lookback_days=400):
    """Returns (pd.Series, error_message). Series is None on failure."""
    client = _get_client()
    if client is None:
        return None, _client_error
    try:
        data = client.get_series(SERIES[name]).dropna()
        if lookback_days and not data.empty:
            cutoff = data.index.max() - pd.Timedelta(days=lookback_days)
            data = data[data.index >= cutoff]
        return data, None
    except Exception as e:
        return None, str(e)


def latest_value(name):
    """Returns (value, as_of_date, error_message). value/as_of_date are None on failure."""
    series, error = fetch_series(name, lookback_days=30)
    if series is None:
        return None, None, error
    if series.empty:
        return None, None, "no data returned"
    return float(series.iloc[-1]), series.index[-1].date(), None
