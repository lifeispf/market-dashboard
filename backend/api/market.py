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

from data import leadership_fetcher

from ._adapter_legacy import legacy_payload
from ._assembly_helpers import _cached_series, _last, _safe, _ytd_slice
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
    """Sectors / RRG / leaders — transitional macro-payload assembly.

    Stage 4 (00_architecture.md §11): the sector RRG metric loop now lives in
    engine/sector/inputs.py:gather_sector_inputs (single source — same RRG
    computation the new SectorEngine and the /api/sectors endpoint use). This
    function maps those rows to the frozen `sectors[]` shape and keeps the
    leaders[] assembly inline (leaders -> Stock tier in Stage 5).

    byte-identical to the pre-retrofit output is guarded by
    engine/tests/test_macro_equivalence.py: gather_sector_inputs uses the same
    DB read-through cache keys, so same-day data is identical.
    """
    from engine.sector.inputs import gather_sector_inputs, sector_rows_to_payload

    sectors_out = sector_rows_to_payload(gather_sector_inputs(market))

    registry = inputs.registry
    sectors_config = inputs.sectors_config
    as_of = inputs.as_of
    sector_defs = sectors_config[market]["sectors"]

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
