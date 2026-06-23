"""engine/macro/eps_source.py — forward-EPS proxy (Phase D-② of
planning/elegant-soaring-twilight.md).

`engine/macro/inputs.py` reads forward EPS via `data/manual.get_override`,
which is None unless an operator has typed a number into config.json's
`manual_overrides`. That leaves the "유동성 천장"(liquidity ceiling) thesis
permanently dark (`bands`/`position`/`fwdPER` all null) in any environment
without a manual override.

This module is a NON-protected, best-effort *approximation*: it derives an
implied forward EPS from a sector/index ETF proxy's forward P/E multiple
(`implied_eps = index_level / proxy_forward_pe`). It is explicitly NOT a
consensus analyst EPS estimate -- it borrows the proxy ETF's forward (or
trailing, as a fallback) P/E and applies it to the *actual* index level, which
assumes the ETF's multiple is a reasonable stand-in for the index's. That
assumption can be wrong (ETF composition != index composition, e.g. QQQ vs the
full NASDAQ Composite), so treat any value from this module as a rough
estimate, not ground truth. Callers/labels should say "추정" (estimated) when
this source is used.

Never raises: every yfinance access is wrapped in try/except -> None, matching
the project's graceful-degradation contract (no network/no key => None, same
as the manual-override path it supplements).
"""
from __future__ import annotations

import yfinance as yf

# Proxy ticker per market: a single liquid ETF whose forward (or trailing)
# P/E we use as a stand-in multiple for the actual index. KOSPI's "EWY" is the
# iShares MSCI South Korea ETF -- not KOSPI itself, but the closest liquid,
# free, yfinance-covered proxy.
_PROXY_TICKER = {
    "NASDAQ": "QQQ",
    "KOSPI": "EWY",
}


def _positive_float(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if x > 0 else None


def fetch_forward_eps(market: str, level: float | None) -> float | None:
    """Derive an implied forward EPS for `market` from its ETF proxy's forward P/E.

    implied_eps = level / forward_pe (falls back to trailing_pe if forward_pe is
    unavailable). Returns None whenever any input is missing/non-positive or the
    yfinance call fails for any reason -- this function never raises.

    This is an APPROXIMATION: a single ETF's P/E proxy for an index, not a
    consensus analyst EPS estimate (no free source for that exists). Use only
    to light up the ceiling band/reconciliation when no manual override is
    present; prefer a manual override when one is available (caller decides).
    """
    level = _positive_float(level)
    if level is None:
        return None

    ticker = _PROXY_TICKER.get(market)
    if not ticker:
        return None

    try:
        info = yf.Ticker(ticker).info
    except Exception:
        return None
    if not info:
        return None

    forward_pe = _positive_float(info.get("forwardPE"))
    pe = forward_pe if forward_pe is not None else _positive_float(info.get("trailingPE"))
    if pe is None:
        return None

    return level / pe
