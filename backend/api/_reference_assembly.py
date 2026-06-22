"""backend/api/_reference_assembly.py — frozen regression oracle.

Stage 2 (Macro retrofit, planning/blueprint_unified/00_architecture.md §5/§11):
this is a VERBATIM copy of backend/api/market.py's pre-retrofit `_assemble_live`
body, renamed to `assemble_live_reference`. Shared plumbing helpers are imported
from backend/api/_assembly_helpers.py instead of being redefined.

THIS FILE MUST NEVER CHANGE AGAIN once the retrofit lands. It is the permanent
deep-equal baseline that the new engine-routed path (engine/macro/ + market.py's
new _assemble_live) is checked against in engine/tests/test_macro_equivalence.py.
Do not "fix" or "improve" anything in here -- if a bug is ever found in this
logic, fix it in the real engine path and leave this oracle frozen (or, if the
oracle itself must move on, that is a deliberate decision for a human to make,
not an incidental edit).

No calculation logic was changed when this file was created -- every line below
is a direct copy of the monolith that GET /api/market/{market} used to run.
"""
from datetime import date

import scoring
from backend import scoring_ext
from backend.store import db, series_map
from config_loader import load_config, load_sectors
from data import kr_fetcher, leadership_fetcher, manual

from ._assembly_helpers import (
    _as_of_str,
    _cached_market_cap,
    _cached_series,
    _last,
    _safe,
    _stale,
    _ytd_slice,
)

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


def assemble_live_reference(market: str) -> dict:
    config = load_config()
    sectors_config = load_sectors()
    registry = series_map.build_registry(market, sectors_config)
    today = date.today()

    index_id = series_map.index_series_id(market)
    index_fetch_fn, index_source = registry[index_id]
    level_series = _cached_series(index_id, index_fetch_fn, index_source, lookback_days=400)
    level = _last(level_series)
    as_of = _as_of_str(level_series) or today.isoformat()

    if market == "KOSPI":
        # series_map stashes which source (KRX vs Yahoo Finance fallback) actually won the
        # last time the KOSPI fetch_fn ran, so we don't need a second live call just for
        # provenance. On a cold process whose DB is already current for today (fetch_fn
        # never ran this request), default to "Yahoo Finance" -- the historically more
        # likely winner given the KRX_ID/KRX_PW auth wall (matches kr_fetcher's own bias).
        source_label = series_map.last_kospi_index_source["value"] or "Yahoo Finance"
        eps_key = "KOSPI_forward_eps"
        anchors = config["multiple_anchors"]["KOSPI"]
    else:
        source_label = "Yahoo Finance"
        eps_key = "NASDAQ_forward_eps"
        anchors = config["multiple_anchors"]["NASDAQ"]

    forward_eps, eps_as_of, _eps_missing = manual.get_override(config, eps_key)
    position = scoring.band_position(level, forward_eps, anchors) if level is not None else None
    levels = scoring.ceiling_levels(forward_eps, anchors)

    # ---- Flow layer ----
    chg_1d_pct = yoy_pct = None
    if level_series is not None and len(level_series) >= 2:
        chg_1d_pct = (level_series.iloc[-1] / level_series.iloc[-2] - 1) * 100
    ytd_for_yoy = level_series.iloc[-252:] if level_series is not None and len(level_series) >= 252 else level_series
    if ytd_for_yoy is not None and len(ytd_for_yoy) >= 2:
        yoy_pct = (ytd_for_yoy.iloc[-1] / ytd_for_yoy.iloc[0] - 1) * 100

    breadth_text = breadth_note = None
    vol_value = None
    vol_label = "VKOSPI(근사·실현변동성)" if market == "KOSPI" else "VIX"
    trailing_per = None
    advancers = decliners = None
    sector_ups = sector_downs = 0

    if market == "KOSPI":
        trailing_per, _fwd_xcheck, _fund_as_of, _fund_err = _safe(
            kr_fetcher.fetch_kospi_fundamental, (None, None, None, None)
        )
        advancers, decliners, _breadth_as_of, _breadth_err = _safe(kr_fetcher.fetch_breadth, (None, None, None, None))
        if advancers is not None:
            breadth_text = f"상승 {advancers} · 하락 {decliners}"
        vol_value = scoring.realized_volatility(level_series, window=20)
    else:
        nasdaq_sectors = sectors_config["NASDAQ"]["sectors"]
        sector_ups = sector_downs = 0
        for sdef in nasdaq_sectors.values():
            etf = sdef.get("etf")
            if not etf or etf not in registry:
                continue
            etf_fetch_fn, etf_source = registry[etf]
            etf_series = _cached_series(etf, etf_fetch_fn, etf_source, lookback_days=10)
            if etf_series is not None and len(etf_series) >= 2:
                if etf_series.iloc[-1] > etf_series.iloc[-2]:
                    sector_ups += 1
                elif etf_series.iloc[-1] < etf_series.iloc[-2]:
                    sector_downs += 1
        breadth_text = f"섹터 {sector_ups}개 상승 · {sector_downs}개 하락"
        vix_series = _cached_series("fred:vix", *registry["fred:vix"], lookback_days=30)
        vol_value = _last(vix_series)

    spark = [round(v, 2) for v in level_series.iloc[-60:].tolist()] if level_series is not None and len(level_series) >= 2 else []
    vol_dir = scoring.trend_direction(level_series, lookback=5) or "flat"

    # ---- S01-S06 raw inputs (market-independent FRED + KR-specific) ----
    walcl = _cached_series("fred:fed_balance_sheet", *registry["fred:fed_balance_sheet"], lookback_days=180)
    fed_dot_plot_2026_cut, _dot_as_of, _ = manual.get_override(config, "fed_dot_plot_2026_cut")
    fed_hike_priced_pct, _hike_as_of, _ = manual.get_override(config, "fed_hike_priced_pct")

    netbuy_df, _netbuy_err = _safe(lambda: kr_fetcher.fetch_foreign_institutional_netbuy(20), (None, None))
    foreign_series = None
    if netbuy_df is not None and "외국인합계" in netbuy_df.columns:
        foreign_series = netbuy_df["외국인합계"]
    foreign_ownership_zscore, _own_as_of, _ = manual.get_override(config, "foreign_ownership_zscore")

    credit_value, credit_as_of, _credit_missing = manual.get_override(config, "credit_balance_krw")
    market_cap, _mc_as_of, _mc_err = _safe(kr_fetcher.fetch_kospi_total_market_cap, (None, None, None))
    if market_cap is None:
        market_cap, _, _ = manual.get_override(config, "kospi_total_market_cap_krw")

    mmf_value, _mmf_as_of, _ = manual.get_override(config, "mmf_total_usd")
    real_rate_series = _cached_series("fred:real_rate_2y", *registry["fred:real_rate_2y"], lookback_days=30)
    real_rate = _last(real_rate_series)

    fx_series = _cached_series("fred:usdkrw", *registry["fred:usdkrw"], lookback_days=90)
    usdkrw = _last(fx_series)

    oas_series = _cached_series("fred:hy_oas", *registry["fred:hy_oas"], lookback_days=180)
    vix_series_for_s06 = _cached_series("fred:vix", *registry["fred:vix"], lookback_days=30)
    hy_oas = _last(oas_series)
    vix_value = _last(vix_series_for_s06)

    TH = config["thresholds"]
    s01_score = scoring.score_s01_central_bank(walcl, fed_dot_plot_2026_cut, fed_hike_priced_pct, TH["S01_central_bank"])
    s02_score = scoring.score_s02_foreign_flow(foreign_ownership_zscore, usdkrw, TH["S02_foreign_flow_KR"])
    s03_score = scoring.score_s03_domestic_credit(credit_value, market_cap, TH["S03_domestic_credit_KR"])
    s04_score = scoring.score_s04_dry_powder(mmf_value, real_rate, TH["S04_us_dry_powder"])
    s05_score = scoring.score_s05_fx(usdkrw, TH["S05_fx_KRW"])
    s06_score = scoring.score_s06_global_credit(hy_oas, vix_value, TH["S06_global_credit"])

    s01_dir = scoring.trend_direction(walcl, lookback=4) if walcl is not None else None
    s02_dir = scoring.cumulative_sign(foreign_series, lookback=5) if foreign_series is not None else None
    s05_dir = scoring.trend_direction(fx_series, lookback=5) if fx_series is not None else None
    s06_dir = scoring.trend_direction(oas_series, lookback=5) if oas_series is not None else None
    vix_dir = scoring.trend_direction(vix_series_for_s06, lookback=5) if vix_series_for_s06 is not None else None

    weights = config["weights"][market]
    subscores = {"S01": s01_score, "S02": s02_score, "S03": s03_score, "S04": s04_score, "S05": s05_score, "S06": s06_score}
    composite, n_avail, n_total = scoring.composite_score(subscores, weights)
    regime = scoring.regime_from_score(composite, config["regime_cuts"])

    recon = scoring.reconciliation_status(position["band"] if position else None, regime)
    supported_ceiling = scoring.liquidity_supported_ceiling(levels, regime) if levels else None

    # persist today's scores (survives restart; feeds future history views)
    _safe(lambda: db.upsert_scores(market, today, subscores, composite, regime, n_avail))

    # ---- §13-1 Fear & Greed ----
    sma_125 = float(level_series.iloc[-125:].mean()) if level_series is not None and len(level_series) >= 125 else None
    if market == "KOSPI":
        up_ratio = (
            advancers / (advancers + decliners)
            if advancers is not None and decliners is not None and (advancers + decliners) > 0
            else None
        )
        fg_vol_input = vol_value  # realized-vol approximation (already computed above)
    else:
        sector_total = sector_ups + sector_downs
        up_ratio = sector_ups / sector_total if sector_total > 0 else None
        fg_vol_input = vix_value

    fear_greed = scoring_ext.fear_greed(
        price=level, sma_125=sma_125, up_ratio=up_ratio,
        vix_or_vkospi=fg_vol_input, hy_oas=hy_oas, fg_config=config["fear_greed"],
    )

    # ---- Sectors / RRG / leaders ----
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

    # ---- Narrative (auto-generated from the live values computed above) ----
    flow_parts = [p for p in [breadth_text, f"YoY {yoy_pct:+.0f}%" if yoy_pct is not None else None] if p]
    flow_narrative = " · ".join(flow_parts) if flow_parts else "데이터 부족"

    if regime and position:
        liquidity_narrative = f"{REGIME_LABEL[regime]} (천장까지 {position['distance_pct']:+.0f}%)"
    elif regime:
        liquidity_narrative = REGIME_LABEL[regime]
    else:
        liquidity_narrative = "산정 불가"

    leading = sorted(
        [r for r in sector_rows if r["quadrant"] == "leading" and r["ytd"] is not None],
        key=lambda r: r["ytd"], reverse=True,
    )
    improving = sorted(
        [r for r in sector_rows if r["quadrant"] == "improving" and r["rs_momentum"] is not None],
        key=lambda r: r["rs_momentum"], reverse=True,
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

    # ---- Sources block ----
    sources_out = []
    score_map = {"S01": s01_score, "S02": s02_score, "S03": s03_score, "S04": s04_score, "S05": s05_score, "S06": s06_score}
    dir_map = {"S01": s01_dir, "S02": s02_dir, "S03": None, "S04": None, "S05": s05_dir, "S06": s06_dir}
    state_map = {
        "S01": f"WALCL ${_last(walcl) / 1e6:.2f}T" if walcl is not None else "데이터 없음 (FRED_API_KEY 필요)",
        "S02": f"외국인 순매수(KOSPI) {foreign_series.iloc[-1] / 1e8:,.0f}억" if foreign_series is not None else "데이터 없음 (KRX 인증 필요)",
        "S03": f"신용잔고 {credit_value / 1e12:,.1f}조" if credit_value else "미입력 (manual_overrides.credit_balance_krw)",
        "S04": f"MMF ${mmf_value / 1e12:,.2f}T" if mmf_value else "미입력 (manual_overrides.mmf_total_usd)",
        "S05": f"USD/KRW {usdkrw:,.1f}" if usdkrw is not None else "데이터 없음 (FRED_API_KEY 필요)",
        "S06": f"HY OAS {hy_oas:.2f}% · VIX {vix_value:.1f}" if hy_oas is not None and vix_value is not None else "데이터 없음 (FRED_API_KEY 필요)",
    }
    DIR_WORD = {"up": "상승", "down": "하락", "flat": "보합", None: "추세 불명"}
    for sid in ("S01", "S02", "S03", "S04", "S05", "S06"):
        meta = dict(SOURCE_META[sid])
        if market == "NASDAQ":
            meta.update(SOURCE_META_NASDAQ_OVERRIDES.get(sid, {}))
        d = dir_map.get(sid)
        score = score_map[sid]
        if score is None:
            headroom_word = "데이터 부족"
        elif score >= 60:
            headroom_word = "여력 높음"
        elif score >= 35:
            headroom_word = "여력 중간"
        else:
            headroom_word = "여력 낮음"
        sources_out.append({
            "id": sid, "name": meta["name"], "scope": meta["scope"],
            "headroom": round(score, 1) if score is not None else None,
            "dir": d or "flat", "dirLabel": f"{DIR_WORD[d]} · {headroom_word}",
            "state": state_map[sid], "score": round(score, 1) if score is not None else None,
        })

    # ---- Watchlist ----
    watchlist_ctx = {
        "fed_dot_plot_2026_cut": fed_dot_plot_2026_cut,
        "walcl_direction": s01_dir,
        "foreign_netbuy_series": foreign_series,
        "forced_liquidation_event": TH["S03_domestic_credit_KR"].get("forced_liquidation_event", False),
        "usdkrw": usdkrw,
        "usdkrw_gate_threshold": TH["S02_foreign_flow_KR"]["usdkrw_gate_threshold"],
        "hy_oas_direction": s06_dir,
        "vix_direction": vix_dir,
    }
    watch_rows = scoring.evaluate_watchlist(config["watchlist"], watchlist_ctx)
    watchlist_out = [
        {"label": r["label"], "trigger": r["trigger"], "meaning": r["meaning"], "status": r["status"]}
        for r in watch_rows
    ]

    # ---- Freshness ----
    def series_as_of(series):
        if series is None or len(series) == 0:
            return None
        last = series.index[-1]
        return last.date().isoformat() if hasattr(last, "date") else str(last)

    freshness_out = [
        {"label": f"{market} 지수레벨", "source": source_label, "freq": "daily", "last": as_of,
         "stale": manual.staleness_level(date.fromisoformat(as_of) if as_of else None, "daily", config) == "stale"},
        {"label": "Fed 대차대조표 (WALCL)", "source": "FRED", "freq": "weekly", "last": series_as_of(walcl),
         "stale": _stale(series_as_of(walcl), "weekly", config)},
        {"label": "외국인 순매수 (KOSPI)", "source": "KRX", "freq": "daily", "last": series_as_of(foreign_series),
         "stale": _stale(series_as_of(foreign_series), "daily", config)},
        {"label": "USD/KRW", "source": "FRED", "freq": "daily", "last": series_as_of(fx_series),
         "stale": _stale(series_as_of(fx_series), "daily", config)},
        {"label": "HY OAS", "source": "FRED", "freq": "daily", "last": series_as_of(oas_series),
         "stale": _stale(series_as_of(oas_series), "daily", config)},
        {"label": "VIX", "source": "FRED", "freq": "daily", "last": series_as_of(vix_series_for_s06),
         "stale": _stale(series_as_of(vix_series_for_s06), "daily", config)},
        {"label": f"{market} 선행EPS (manual)", "source": "수동입력", "freq": "quarterly", "last": eps_as_of.isoformat() if eps_as_of else None,
         "stale": manual.staleness_level(eps_as_of, "quarterly", config) == "stale"},
    ]

    # ---- pill / source / final assembly ----
    pill = f"{regime.upper()} regime" if regime else "regime 산정 불가"
    payload = {
        "market": market,
        "asOf": as_of,
        "source": source_label,
        "pill": pill,
        "flow": {
            "level": level, "chgPct": round(chg_1d_pct, 2) if chg_1d_pct is not None else None,
            "yoyPct": round(yoy_pct, 0) if yoy_pct is not None else None,
            "fwdPER": round(scoring.current_multiple(level, forward_eps), 1) if forward_eps and level is not None else None,
            "trailingPER": round(trailing_per, 1) if trailing_per is not None else None,
            "breadthText": breadth_text, "breadthNote": breadth_note,
            "volLabel": vol_label, "volValue": round(vol_value, 1) if vol_value is not None else None,
            "volDir": vol_dir, "spark": spark,
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
