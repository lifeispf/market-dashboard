"""GET /api/market/{market} — the frozen contract endpoint.

Track 0: returned MOCK_PAYLOADS in the frozen contract shape.
Track A: assemble_payload() now builds the payload from LIVE data — the existing
app.py calculation logic (scoring.py + data/*.py fetchers), routed through the
backend/store read-through cache (backend/store/ingest.py + db.py) — while keeping
the returned SHAPE byte-for-byte identical to contract.md / frontend/src/api/types.ts.

Graceful degradation is load-bearing, not optional: with no FRED_API_KEY and no
KRX_ID/KRX_PW set, S01/S03/S04/S05/S06 and KOSPI breadth/foreign-flow/market-cap are
expected to come back null. This module must never 500 — every live lookup is wrapped
so a fetch failure degrades a field to null instead of raising.

TRANSITIONAL (Stage 2, Macro retrofit, planning/blueprint_unified/00_architecture.md
§5/§7/§11): `_assemble_live` now routes through the macro Engine Core path
(engine/macro/inputs.py:gather_macro_inputs + engine/macro/engine.py:build_macro_engine)
instead of running the old monolith inline. `_assemble_sectors_leaders` below still
computes sectors[]/RRG/leaders the exact same way the pre-retrofit monolith did --
01_altitude_separation.md eventually wants this in a separate Sector/Stock Engine, but
for THIS stage the only acceptance criterion is byte-identical output, so it stays
co-located here unmoved (calculation logic unchanged, only relocated -- see
backend/api/_reference_assembly.py for the permanent regression oracle this is checked
against in engine/tests/test_macro_equivalence.py). The legacy MarketPayload shape is
reconstructed by backend/api/_adapter_legacy.py:legacy_payload from the new
EngineOutput + MacroInputs + sectors/leaders -- no calculation happens in this file
anymore, only wiring.
"""
from fastapi import APIRouter, HTTPException

import scoring
from backend.store import db
from data import leadership_fetcher

from ._adapter_legacy import legacy_payload
from ._assembly_helpers import _cached_market_cap, _cached_series, _last, _safe, _ytd_slice
from .mock_data import MOCK_PAYLOADS

router = APIRouter()

VALID_MARKETS = ("KOSPI", "NASDAQ")

# Track A flips this to True once live assembly is wired. Kept as a flag so the
# frontend and integration tests can see which mode the backend is serving.
LIVE_MODE = True


# ---- assembly ---------------------------------------------------------------


def assemble_payload(market: str) -> dict:
    """Builds the full live market payload. Falls back to the mock shape (with
    _mode left as "mock") only if live assembly raises -- which it is designed not
    to, since every external call below is individually guarded."""
    try:
        return _assemble_live(market)
    except Exception as exc:  # last-resort safety net; live assembly should never reach here
        payload = dict(MOCK_PAYLOADS[market])
        payload["_mode"] = f"mock (live assembly failed: {exc})"
        return payload


def _assemble_live(market: str) -> dict:
    """Stage 2: routes through the macro Engine Core path. This function must
    NEVER call backend/api/_reference_assembly.py:assemble_live_reference -- that
    module is the frozen oracle this path is checked against, not a dependency
    of it."""
    from engine.core.context import Context
    from engine.macro.engine import build_macro_engine
    from engine.macro.inputs import gather_macro_inputs
    from engine.macro.rulebook import MacroRulebook

    inputs = gather_macro_inputs(market)

    engine = build_macro_engine()
    engine.rulebook = MacroRulebook(inputs)  # inject this request's raw data source
    engine_output = engine.run(market, Context.root(market), data=inputs)

    sectors_out, leaders_out = _assemble_sectors_leaders(market, inputs)

    return legacy_payload(market, engine_output, inputs, sectors_out, leaders_out)


def _assemble_sectors_leaders(market: str, inputs) -> tuple[list[dict], dict]:
    """Sectors / RRG / leaders — copied verbatim out of the pre-retrofit
    `_assemble_live` monolith (calculation logic unchanged, only relocated into
    its own function so the new engine-routed `_assemble_live` can call it).

    `inputs` is the MacroInputs this request's gather_macro_inputs() already
    produced -- registry/sectors_config/today/level_series are read off it
    instead of being re-fetched, so this performs exactly the same DB
    read-through calls (same cache keys) as the monolith did inline.
    """
    config = inputs.config
    sectors_config = inputs.sectors_config
    registry = inputs.registry
    today = inputs.today
    level_series = inputs.level_series
    as_of = inputs.as_of

    benchmark_series = level_series
    sector_defs = sectors_config[market]["sectors"]
    sector_rows = []
    # app.py uses a single YTD-windowed sector_series for BOTH the YTD% calc and the RRG
    # compute_rs_ratio_momentum() call (cached_ticker_series(etf/tk, "ytd")) -- there is no
    # separate full-history series for sectors at all. compute_rs_ratio_momentum only needs
    # ratio_window+momentum_window+1 (21 by default config) overlapping points, well inside
    # a ~113-170 trading-day YTD window, so mirroring app.py exactly loses nothing here.
    benchmark_ytd = _ytd_slice(benchmark_series)
    for code, sdef in sector_defs.items():
        if "etf" in sdef and sdef["etf"] in registry:
            etf = sdef["etf"]
            fetch_fn, source = registry[etf]
            full_series = _cached_series(etf, fetch_fn, source, lookback_days=400)
            sector_series = _ytd_slice(full_series)
        else:
            const_full = []
            for tk in sdef.get("tickers", []):
                if tk not in registry:
                    continue
                fetch_fn, source = registry[tk]
                const_full.append(_cached_series(tk, fetch_fn, source, lookback_days=400))
            # build_aggregate_series() rebases each constituent to 100 at ITS OWN first
            # point (scoring.py docstring: "each rebased to 100 at its first point") --
            # so constituents must be sliced to the YTD window BEFORE aggregating, mirroring
            # app.py's cached_ticker_series(tk, "ytd") which constrains the fetch itself.
            # Aggregating the full multi-year history first and slicing afterwards anchors
            # the rebase at ~400 days ago instead of Jan 1, inflating YTD% for anything with
            # a multi-year uptrend (caught by the app.py cross-check in verification).
            const_ytd = [_ytd_slice(s) for s in const_full]
            sector_series = scoring.build_aggregate_series(const_ytd)

        market_caps = [_cached_market_cap(tk) for tk in sdef.get("tickers", [])]
        sector_cap = sum(c for c in market_caps if c) or None

        ytd = leadership_fetcher.ytd_pct(sector_series) if sector_series is not None else None
        rs_r, rs_m = (
            scoring.compute_rs_ratio_momentum(
                sector_series, benchmark_ytd,
                ratio_window=config["rrg"]["ratio_window"], momentum_window=config["rrg"]["momentum_window"],
            )
            if sector_series is not None and benchmark_ytd is not None
            else (None, None)
        )
        quadrant = scoring.rrg_quadrant(rs_r, rs_m)
        sector_rows.append({
            "code": code, "name": sdef["name"], "market_cap": sector_cap,
            "ytd": ytd, "rs_ratio": rs_r, "rs_momentum": rs_m, "quadrant": quadrant,
        })
        _safe(lambda code=code, sector_cap=sector_cap, ytd=ytd, rs_r=rs_r, rs_m=rs_m, quadrant=quadrant: db.upsert_sector_metric(
            market, code, today, sector_cap, ytd, rs_r, rs_m, quadrant,
        ))

    sectors_out = [
        {
            "code": r["code"], "name": r["name"], "marketCap": r["market_cap"], "ytd": r["ytd"],
            "rsRatio": r["rs_ratio"], "rsMomentum": r["rs_momentum"], "quadrant": r["quadrant"],
        }
        for r in sector_rows
    ]

    leaders_out = {}
    for code, sdef in sector_defs.items():
        key_tks, star_tks = sdef.get("key", []), sdef.get("star", [])
        if not key_tks and not star_tks:
            continue

        def build_leader(tk):
            price = None
            if tk in registry:
                fetch_fn, source = registry[tk]
                tk_series_full = _cached_series(tk, fetch_fn, source, lookback_days=400)
                price = _last(tk_series_full)
                tk_ytd = leadership_fetcher.ytd_pct(_ytd_slice(tk_series_full))
            else:
                tk_ytd = None
            if price is None:
                price, _cap, _err = _safe(lambda: leadership_fetcher.fetch_ticker_quote(tk), (None, None, None))
            leader_meta = sdef.get("leaders", {}).get(tk, {})
            return {
                "ticker": tk, "name": sdef.get("names", {}).get(tk, tk),
                "role": leader_meta.get("role", ""), "price": price, "ytd": tk_ytd,
                "thesis": leader_meta.get("thesis", ""), "stats": leader_meta.get("stats", []),
                "risk": leader_meta.get("risk", ""), "asOf": leader_meta.get("as_of", as_of),
            }

        leaders_out[code] = {
            "key": [build_leader(tk) for tk in key_tks],
            "star": [build_leader(tk) for tk in star_tks],
        }

    return sectors_out, leaders_out


@router.get("/api/market/{market}")
def get_market(market: str):
    market = market.upper()
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=404, detail=f"unknown market: {market}")
    return assemble_payload(market)
