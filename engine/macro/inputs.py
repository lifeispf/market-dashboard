"""engine/macro/inputs.py — raw data gathering for the macro tier.

Stage 2 (Macro retrofit, planning/blueprint_unified/00_architecture.md §5):
`gather_macro_inputs()` performs the exact same fetch/raw-calculation work that
backend/api/market.py's pre-retrofit `_assemble_live` used to do inline (the
148~292-line region of the monolith covering index level, flow layer, S01-S06
raw inputs/scores/directions, composite/regime/reconciliation, and the §13-1
Fear & Greed inputs) and packages every raw value into a single `MacroInputs`
dataclass.

No calculation logic changed here -- every expression below is copied verbatim
from the pre-retrofit monolith. This module ONLY gathers; it does not interpret
(that's engine/macro/modules/*.py) and does not decide a verdict (that's
engine/macro/rulebook.py).

`MacroInputs` deliberately keeps every raw value the legacy adapter
(backend/api/_adapter_legacy.py) needs to reconstruct the frozen MarketPayload
byte-for-byte -- including values modules don't directly need (e.g. `registry`,
`sectors_config`, `today`) but the still-transitional sectors/leaders assembly
(`backend/api/market.py:_assemble_sectors_leaders`) does.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import scoring
from backend import scoring_ext
from backend.store import db, series_map
from config_loader import load_config, load_sectors
from data import kr_fetcher, manual
from engine.core.timeframes import lookback_days_for, normalize_tf, resample_for_tf, spark_n_for
from engine.macro import eps_source, vkospi_source

from backend.api._assembly_helpers import _cached_series, _last, _as_of_str, _safe


@dataclass
class MacroInputs:
    """모든 원시 시리즈/스칼라 — macro tier의 모듈/rulebook/레거시 어댑터가
    소비하는 단일 원천. _assemble_live의 fetch/원시계산 영역을 그대로
    옮긴 결과를 보존한다 (계산식 변경 없음)."""

    market: str
    today: date

    # ---- config / registry (transitional sectors/leaders 빌드에도 필요) ----
    config: dict[str, Any]
    sectors_config: dict[str, Any]
    registry: dict[str, Any]

    # ---- index level ----
    level_series: Any
    level: float | None
    as_of: str
    source_label: str

    # ---- index valuation ----
    forward_eps: float | None
    eps_as_of: date | None
    anchors: dict[str, Any]
    position: dict[str, Any] | None
    levels: dict[str, tuple[float, float]] | None

    # ---- flow layer ----
    chg_1d_pct: float | None
    yoy_pct: float | None
    breadth_text: str | None
    breadth_note: str | None
    vol_value: float | None
    vol_label: str
    vol_dir: str
    trailing_per: float | None
    advancers: int | None
    decliners: int | None
    sector_ups: int
    sector_downs: int
    spark: list[float]

    # ---- S01-S06 raw inputs ----
    walcl: Any
    fed_dot_plot_2026_cut: bool | None
    fed_hike_priced_pct: float | None
    foreign_series: Any
    foreign_ownership_zscore: float | None
    credit_value: float | None
    credit_as_of: date | None
    market_cap: float | None
    mmf_value: float | None
    real_rate_series: Any
    real_rate: float | None
    fx_series: Any
    usdkrw: float | None
    oas_series: Any
    vix_series_for_s06: Any
    hy_oas: float | None
    vix_value: float | None

    # ---- S01-S06 scores + directions ----
    s01_score: float | None
    s02_score: float | None
    s03_score: float | None
    s04_score: float | None
    s05_score: float | None
    s06_score: float | None
    s01_dir: str | None
    s02_dir: str | None
    s05_dir: str | None
    s06_dir: str | None
    vix_dir: str | None

    # ---- composite / regime / reconciliation ----
    weights: dict[str, float]
    subscores: dict[str, float | None]
    composite: float | None
    n_avail: int
    n_total: int
    regime: str | None
    recon: str | None
    supported_ceiling: float | None

    # ---- §13-1 Fear & Greed ----
    sma_125: float | None
    up_ratio: float | None
    fg_vol_input: float | None
    fear_greed: dict[str, Any] = field(default_factory=dict)


def gather_macro_inputs(market: str, tf: str = "1D") -> MacroInputs:
    """_assemble_live의 fetch/원시계산 영역을 그대로 수행해 MacroInputs를 채운다.

    계산식은 한 글자도 바꾸지 않는다 -- 아래 본문은 backend/api/market.py의
    pre-retrofit `_assemble_live` 본문에서 sectors/leaders/narrative/sources/
    watchlist/freshness/payload 조립 부분을 제외한, 데이터 수집과 S01-S06/
    fear_greed 산출 영역의 정확한 복사다.

    Phase A: `tf`는 ONLY `spark`에 영향을 준다 (Class A 윈도우-종속 지표 중 이
    모듈이 노출하는 유일한 필드). vol_value/yoy_pct/S01-S06/fear_greed 등은 Phase
    A 범위 밖(Class B — 점수-추세는 history.py가 별도로 다룸)이라 tf="1D" 기본값
    경로와 동일하게 그대로 둔다. tf="1D"는 resample_for_tf가 identity이므로 spark도
    기존 `level_series.iloc[-60:]`와 byte-identical하다.
    """
    tf = normalize_tf(tf)
    config = load_config()
    sectors_config = load_sectors()
    registry = series_map.build_registry(market, sectors_config)
    today = date.today()

    index_id = series_map.index_series_id(market)
    index_fetch_fn, index_source = registry[index_id]
    level_series = _cached_series(index_id, index_fetch_fn, index_source, lookback_days=lookback_days_for(tf))
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

    # ---- D-② new live input: forward-EPS proxy fetch (engine/macro/eps_source.py) ----
    # manual.get_override only returns a value if an operator typed one into
    # config.json's manual_overrides (almost never true in practice), which left the
    # ceiling band/reconciliation/fwdPER permanently null. When no manual override is
    # present, try a best-effort ETF-proxy-derived implied forward EPS instead (see
    # eps_source.py docstring for the approximation caveat). This is a NEW live input
    # outside the retrofit's frozen-oracle scope (test_macro_equivalence monkeypatches
    # it to None so the byte-identical gate still validates pre-existing logic parity).
    # Cached via the existing read-through series pattern (series_id="eps:{market}")
    # so we don't hit yfinance on every request.
    if forward_eps is None:
        eps_series_id = f"eps:{market}"

        def _eps_fetch_fn(_lookback_days, _level=level, _market=market):
            value = eps_source.fetch_forward_eps(_market, _level)
            return [(today, value)] if value is not None else []

        eps_proxy_series = _cached_series(eps_series_id, _eps_fetch_fn, "yfinance(proxy,추정)", lookback_days=1)
        eps_proxy_value = _last(eps_proxy_series)
        if eps_proxy_value is not None:
            forward_eps = eps_proxy_value
            eps_as_of = date.fromisoformat(_as_of_str(eps_proxy_series) or today.isoformat())

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
    kospi_vol_is_vkospi = False  # KOSPI F3가 실제 VKOSPI인지(→ F3 anchor 재보정 분기)
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
        # F3 변동성: 실제 VKOSPI(코스피200 변동성지수, KRX OpenAPI) 우선 — implied-vol
        # 지수라 realized-vol 근사보다 정합적. 무키/미신청/실패 시 realized vol로 폴백.
        vkospi = vkospi_source.fetch_vkospi()
        if vkospi is not None:
            vol_value = vkospi
            vol_label = "VKOSPI"
            kospi_vol_is_vkospi = True
        else:
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

    spark_series = resample_for_tf(level_series, tf)
    spark = (
        [round(v, 2) for v in spark_series.iloc[-spark_n_for(tf):].tolist()]
        if spark_series is not None and len(spark_series) >= 2
        else []
    )
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

    # F3 anchor 보정: VKOSPI(코스피200 변동성지수)는 이 데이터셋에서 ~20(평온)~95(위기)
    # 범위라, VIX 기준 anchor(lo12/hi30)면 대부분 0에 saturate. KOSPI가 실제 VKOSPI를
    # 쓸 때만 in-memory로 F3 anchor를 VKOSPI 분포(lo20/hi80)에 맞춘다(config.json 무수정;
    # NASDAQ/VIX·realized-vol 폴백 경로는 기존 anchor 그대로).
    fg_config = config["fear_greed"]
    if kospi_vol_is_vkospi:
        import copy

        fg_config = copy.deepcopy(fg_config)
        fg_config["anchors"]["F3_vol"] = {"lo": 20, "hi": 80, "invert": True}

    fear_greed = scoring_ext.fear_greed(
        price=level, sma_125=sma_125, up_ratio=up_ratio,
        vix_or_vkospi=fg_vol_input, hy_oas=hy_oas, fg_config=fg_config,
    )

    return MacroInputs(
        market=market,
        today=today,
        config=config,
        sectors_config=sectors_config,
        registry=registry,
        level_series=level_series,
        level=level,
        as_of=as_of,
        source_label=source_label,
        forward_eps=forward_eps,
        eps_as_of=eps_as_of,
        anchors=anchors,
        position=position,
        levels=levels,
        chg_1d_pct=chg_1d_pct,
        yoy_pct=yoy_pct,
        breadth_text=breadth_text,
        breadth_note=breadth_note,
        vol_value=vol_value,
        vol_label=vol_label,
        vol_dir=vol_dir,
        trailing_per=trailing_per,
        advancers=advancers,
        decliners=decliners,
        sector_ups=sector_ups,
        sector_downs=sector_downs,
        spark=spark,
        walcl=walcl,
        fed_dot_plot_2026_cut=fed_dot_plot_2026_cut,
        fed_hike_priced_pct=fed_hike_priced_pct,
        foreign_series=foreign_series,
        foreign_ownership_zscore=foreign_ownership_zscore,
        credit_value=credit_value,
        credit_as_of=credit_as_of,
        market_cap=market_cap,
        mmf_value=mmf_value,
        real_rate_series=real_rate_series,
        real_rate=real_rate,
        fx_series=fx_series,
        usdkrw=usdkrw,
        oas_series=oas_series,
        vix_series_for_s06=vix_series_for_s06,
        hy_oas=hy_oas,
        vix_value=vix_value,
        s01_score=s01_score,
        s02_score=s02_score,
        s03_score=s03_score,
        s04_score=s04_score,
        s05_score=s05_score,
        s06_score=s06_score,
        s01_dir=s01_dir,
        s02_dir=s02_dir,
        s05_dir=s05_dir,
        s06_dir=s06_dir,
        vix_dir=vix_dir,
        weights=weights,
        subscores=subscores,
        composite=composite,
        n_avail=n_avail,
        n_total=n_total,
        regime=regime,
        recon=recon,
        supported_ceiling=supported_ceiling,
        sma_125=sma_125,
        up_ratio=up_ratio,
        fg_vol_input=fg_vol_input,
        fear_greed=fear_greed,
    )
