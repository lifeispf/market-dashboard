"""backend/api/_adapter_legacy.py — EngineOutput -> frozen MarketPayload.

Stage 2 (Macro retrofit, planning/blueprint_unified/00_architecture.md §5/§7.3):
`legacy_payload()` reconstructs the exact MarketPayload shape that
backend/api/contract.md freezes, from the new engine-routed
EngineOutput + MacroInputs + (transitional) sectors/leaders -- byte-identical
to what backend/api/_reference_assembly.py:assemble_live_reference() produces.

No new calculation happens here. Every value below is read off either
`engine_output` (the macro tier's Verdict/ModuleOutput) or `inputs`
(MacroInputs, the same raw-data source the modules computed from) and
formatted exactly as backend/api/market.py's pre-retrofit `_assemble_live`
used to format it.

payload["_mode"] is hardcoded to "live" (matching the frozen contract's
existing behavior) -- engine_output.mode (which can be "degraded") is an
internal Engine Core concept (00_architecture.md §9.3) that is NOT exposed in
the frozen payload shape; contract.md's `_mode` predates Engine Core and means
something different ("mock" vs "live" data source, not module health).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.core.contracts import EngineOutput
    from engine.macro.inputs import MacroInputs

REGIME_LABEL = {
    "base": "BASE only — 멀티플 유지가 한계",
    "bull": "BULL 도달가능 — 재평가 연료 부분충전",
    "hyper": "HYPER 연료 존재 — 지속가능성은 별도 경고",
}
RECON_SYMBOL = {"aligned": "🟢", "overheated": "🔴", "slack": "🟡"}
RECON_TEXT = {"aligned": "정합", "overheated": "과열", "slack": "여유"}
SOURCE_META = {
    "S01": {"name": "중앙은행 정책", "scope": "Fed · BOK"},
    "S02": {"name": "외국인 자금", "scope": "KOSPI 한정"},
    "S03": {"name": "국내 신용·레버리지", "scope": "KOSPI · KOSDAQ"},
    "S04": {"name": "美 대기자금·자사주", "scope": "글로벌 공통배경"},
    "S05": {"name": "원/달러 환율", "scope": "증폭기 / 게이트"},
    "S06": {"name": "글로벌 신용·금융환경", "scope": "공통 배경"},
}
SOURCE_META_NASDAQ_OVERRIDES = {
    "S01": {"scope": "Fed"},
    "S02": {"name": "외국인 자금(참고)", "scope": "간접 배경"},
    "S03": {"name": "신용·레버리지(마진)", "scope": "글로벌 참고"},
    "S04": {"scope": "NASDAQ 핵심"},
    "S05": {"name": "달러지수(DXY)", "scope": "글로벌 배경"},
    "S06": {"scope": "핵심 배경"},
}
DIR_WORD = {"up": "상승", "down": "하락", "flat": "보합", None: "추세 불명"}

# macro.S0X module_id -> the 2-char source id used by the frozen `sources[]` block.
_MODULE_TO_SID = {
    "macro.S01": "S01", "macro.S02": "S02", "macro.S03": "S03",
    "macro.S04": "S04", "macro.S05": "S05", "macro.S06": "S06",
}


def _headroom_word(score: float | None) -> str:
    if score is None:
        return "데이터 부족"
    if score >= 60:
        return "여력 높음"
    if score >= 35:
        return "여력 중간"
    return "여력 낮음"


def legacy_payload(
    market: str,
    engine_output: "EngineOutput",
    inputs: "MacroInputs",
    sectors_out: list[dict[str, Any]],
    leaders_out: dict[str, Any],
) -> dict:
    """Reconstructs the frozen MarketPayload from the new engine-routed output.

    Args:
        market: "KOSPI" | "NASDAQ".
        engine_output: build_macro_engine().run(...) 결과(verdict.extra에
            composite/regime/reconciliation/supportedCeiling/position/levels/
            fear_greed가 들어있다).
        inputs: 이 실행의 MacroInputs(gather_macro_inputs 출력) -- flow/
            sources/watchlist/freshness/narrative 재구성에 쓰는 원시값 전부.
        sectors_out: transitional sector rows (이미 frozen `sectors[]` shape).
        leaders_out: transitional leaders dict (이미 frozen `leaders{}` shape).

    Returns:
        contract.md가 동결한 MarketPayload와 byte-identical한 dict.
    """
    extra = engine_output.verdict.extra
    regime = extra.get("regime")
    composite = extra.get("composite")
    n_avail = extra.get("n_avail")
    n_total = extra.get("n_total")
    recon = extra.get("reconciliation")
    supported_ceiling = extra.get("supportedCeiling")
    position = extra.get("position")
    levels = extra.get("levels")
    fear_greed = extra.get("fear_greed")

    level = inputs.level
    forward_eps = inputs.forward_eps
    as_of = inputs.as_of
    source_label = inputs.source_label

    # ---- Narrative (auto-generated from the live values, mirrors pre-retrofit _assemble_live) ----
    flow_parts = [
        p for p in [inputs.breadth_text, f"YoY {inputs.yoy_pct:+.0f}%" if inputs.yoy_pct is not None else None]
        if p
    ]
    flow_narrative = " · ".join(flow_parts) if flow_parts else "데이터 부족"

    if regime and position:
        liquidity_narrative = f"{REGIME_LABEL[regime]} (천장까지 {position['distance_pct']:+.0f}%)"
    elif regime:
        liquidity_narrative = REGIME_LABEL[regime]
    else:
        liquidity_narrative = "산정 불가"

    leading = sorted(
        [r for r in sectors_out if r["quadrant"] == "leading" and r["ytd"] is not None],
        key=lambda r: r["ytd"], reverse=True,
    )
    improving = sorted(
        [r for r in sectors_out if r["quadrant"] == "improving" and r["rsMomentum"] is not None],
        key=lambda r: r["rsMomentum"], reverse=True,
    )
    leadership_parts = []
    if leading:
        leadership_parts.append(f"{leading[0]['name']} 견인")
    if improving:
        leadership_parts.append(f"{improving[0]['name']} 순환매 진입 후보")
    leadership_narrative = " · ".join(leadership_parts) if leadership_parts else "뚜렷한 주도 섹터 없음"

    if recon:
        recon_narrative = f"{RECON_SYMBOL[recon]} {RECON_TEXT[recon]}"
    else:
        recon_narrative = "⚪ 산정 불가"

    # ---- Sources block — rebuilt from each macro.S0X ModuleOutput.inputs ----
    module_by_sid = {
        _MODULE_TO_SID[m.module_id]: m for m in engine_output.modules if m.module_id in _MODULE_TO_SID
    }
    sources_out = []
    for sid in ("S01", "S02", "S03", "S04", "S05", "S06"):
        meta = dict(SOURCE_META[sid])
        if market == "NASDAQ":
            meta.update(SOURCE_META_NASDAQ_OVERRIDES.get(sid, {}))
        module_output = module_by_sid.get(sid)
        m_inputs = module_output.inputs if module_output is not None else {}
        d = m_inputs.get("raw_dir")
        score = m_inputs.get("raw_score")
        state_text = m_inputs.get("state_text")
        sources_out.append({
            "id": sid, "name": meta["name"], "scope": meta["scope"],
            "headroom": round(score, 1) if score is not None else None,
            "dir": d or "flat", "dirLabel": f"{DIR_WORD[d]} · {_headroom_word(score)}",
            "state": state_text, "score": round(score, 1) if score is not None else None,
        })

    # ---- Watchlist ----
    import scoring  # local import mirrors the pre-retrofit module's own lazy-safe style

    TH = inputs.config["thresholds"]
    watchlist_ctx = {
        "fed_dot_plot_2026_cut": inputs.fed_dot_plot_2026_cut,
        "walcl_direction": inputs.s01_dir,
        "foreign_netbuy_series": inputs.foreign_series,
        "forced_liquidation_event": TH["S03_domestic_credit_KR"].get("forced_liquidation_event", False),
        "usdkrw": inputs.usdkrw,
        "usdkrw_gate_threshold": TH["S02_foreign_flow_KR"]["usdkrw_gate_threshold"],
        "hy_oas_direction": inputs.s06_dir,
        "vix_direction": inputs.vix_dir,
    }
    watch_rows = scoring.evaluate_watchlist(inputs.config["watchlist"], watchlist_ctx)
    watchlist_out = [
        {"label": r["label"], "trigger": r["trigger"], "meaning": r["meaning"], "status": r["status"]}
        for r in watch_rows
    ]

    # ---- Freshness ----
    from data import manual

    from ._assembly_helpers import _stale

    def series_as_of(series):
        if series is None or len(series) == 0:
            return None
        last = series.index[-1]
        return last.date().isoformat() if hasattr(last, "date") else str(last)

    from datetime import date as _date

    freshness_out = [
        {"label": f"{market} 지수레벨", "source": source_label, "freq": "daily", "last": as_of,
         "stale": manual.staleness_level(_date.fromisoformat(as_of) if as_of else None, "daily", inputs.config) == "stale"},
        {"label": "Fed 대차대조표 (WALCL)", "source": "FRED", "freq": "weekly", "last": series_as_of(inputs.walcl),
         "stale": _stale(series_as_of(inputs.walcl), "weekly", inputs.config)},
        {"label": "외국인 순매수 (KOSPI)", "source": "KRX", "freq": "daily", "last": series_as_of(inputs.foreign_series),
         "stale": _stale(series_as_of(inputs.foreign_series), "daily", inputs.config)},
        {"label": "USD/KRW", "source": "FRED", "freq": "daily", "last": series_as_of(inputs.fx_series),
         "stale": _stale(series_as_of(inputs.fx_series), "daily", inputs.config)},
        {"label": "HY OAS", "source": "FRED", "freq": "daily", "last": series_as_of(inputs.oas_series),
         "stale": _stale(series_as_of(inputs.oas_series), "daily", inputs.config)},
        {"label": "VIX", "source": "FRED", "freq": "daily", "last": series_as_of(inputs.vix_series_for_s06),
         "stale": _stale(series_as_of(inputs.vix_series_for_s06), "daily", inputs.config)},
        {"label": f"{market} 선행EPS (manual)", "source": "수동입력", "freq": "quarterly",
         "last": inputs.eps_as_of.isoformat() if inputs.eps_as_of else None,
         "stale": manual.staleness_level(inputs.eps_as_of, "quarterly", inputs.config) == "stale"},
    ]

    # ---- pill / source / final assembly ----
    pill = f"{regime.upper()} regime" if regime else "regime 산정 불가"
    payload = {
        "market": market,
        "asOf": as_of,
        "source": source_label,
        "pill": pill,
        "flow": {
            "level": level, "chgPct": round(inputs.chg_1d_pct, 2) if inputs.chg_1d_pct is not None else None,
            "yoyPct": round(inputs.yoy_pct, 0) if inputs.yoy_pct is not None else None,
            "fwdPER": round(scoring.current_multiple(level, forward_eps), 1) if forward_eps and level is not None else None,
            "trailingPER": round(inputs.trailing_per, 1) if inputs.trailing_per is not None else None,
            "breadthText": inputs.breadth_text, "breadthNote": inputs.breadth_note,
            "volLabel": inputs.vol_label, "volValue": round(inputs.vol_value, 1) if inputs.vol_value is not None else None,
            "volDir": inputs.vol_dir, "spark": inputs.spark,
        },
        "bands": (
            {
                "base": {"lo": levels["base"][0], "hi": levels["base"][1]},
                "bull": {"lo": levels["bull"][0], "hi": levels["bull"][1]},
                "hyper": {"lo": levels["hyper"][0], "hi": levels["hyper"][1]},
                "hyperOpen": True,
            }
            if levels is not None else None
        ),
        "regime": {
            "composite": round(composite, 1) if composite is not None else None,
            "label": REGIME_LABEL.get(regime, "N/A"), "nAvailable": n_avail, "nTotal": n_total,
        },
        "fearGreed": fear_greed,
        "reconciliation": {
            "state": recon, "symbol": RECON_SYMBOL.get(recon, "⚪"), "label": RECON_TEXT.get(recon, "산정 불가"),
            "supportedCeiling": supported_ceiling, "priceBand": position["band"] if position else None,
            "distancePct": round(position["distance_pct"], 1) if position else None,
        },
        "sources": sources_out,
        "sectors": sectors_out,
        "leaders": leaders_out,
        "narrative": {
            "flow": flow_narrative, "liquidity": liquidity_narrative,
            "leadership": leadership_narrative, "reconciliation": recon_narrative,
        },
        "watchlist": watchlist_out,
        "freshness": freshness_out,
        "_mode": "live",
    }
    return payload
