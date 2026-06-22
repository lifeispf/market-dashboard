import pandas as pd

BAND_ORDER = ["base", "bull", "hyper"]

DIRECTION_ARROW = {"up": "↗", "down": "↘", "flat": "→"}


def trend_direction(series, lookback=5):
    """Sign of change over the lookback window. Returns 'up' | 'down' | 'flat' | None."""
    if series is None or len(series) < 2:
        return None
    window = series.iloc[-lookback:] if len(series) >= lookback else series
    change = window.iloc[-1] - window.iloc[0]
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "flat"


def cumulative_sign(series, lookback=5):
    """Sign of the sum over the lookback window (e.g. 5-day cumulative net buy). Returns 'up' | 'down' | 'flat' | None."""
    if series is None or len(series) == 0:
        return None
    total = series.iloc[-lookback:].sum()
    if total > 0:
        return "up"
    if total < 0:
        return "down"
    return "flat"


def ceiling_levels(forward_eps, anchors):
    """index = forward_eps x multiple. Returns {scenario: (lo, hi)} or None if eps missing."""
    if not forward_eps:
        return None
    return {
        scenario: (forward_eps * lo, forward_eps * hi)
        for scenario, (lo, hi) in anchors.items()
    }


def current_multiple(current_index, forward_eps):
    if not forward_eps or not current_index:
        return None
    return current_index / forward_eps


def band_position(current_index, forward_eps, anchors):
    """Finds the nearest ceiling at/above the current index.

    Returns {"band", "ceiling", "distance_pct"} or None if inputs are missing.
    distance_pct is negative when current_index has overshot the hyper ceiling.
    """
    levels = ceiling_levels(forward_eps, anchors)
    if levels is None or not current_index:
        return None

    for scenario in BAND_ORDER:
        _, hi = levels[scenario]
        if current_index <= hi:
            return {
                "band": scenario,
                "ceiling": hi,
                "distance_pct": (hi - current_index) / current_index * 100,
            }

    _, hyper_hi = levels["hyper"]
    return {
        "band": "above_hyper",
        "ceiling": hyper_hi,
        "distance_pct": (hyper_hi - current_index) / current_index * 100,
    }


def _clamp(score, lo=0, hi=100):
    return max(lo, min(hi, score))


def _linear_band(value, lo_value, hi_value, score_at_lo, score_at_hi):
    """Linearly interpolates a score as value moves from lo_value to hi_value, clamped at the ends."""
    if lo_value == hi_value:
        return score_at_lo
    frac = (value - lo_value) / (hi_value - lo_value)
    frac = max(0.0, min(1.0, frac))
    return score_at_lo + frac * (score_at_hi - score_at_lo)


# ---- §4-1 원천별 여력 서브점수 (0-100) ----


def score_s01_central_bank(walcl_series, dot_plot_2026_cut, hike_priced_pct, thresholds):
    """dot_plot_2026_cut: bool|None (manual). hike_priced_pct: 0-100|None (manual)."""
    score = thresholds["base_score"]
    if dot_plot_2026_cut:
        score += thresholds["dot_plot_2026_cut_bonus"]
    if walcl_series is not None and len(walcl_series) >= 2:
        lookback = thresholds["walcl_trend_lookback_weeks"]
        window = walcl_series.iloc[-lookback:] if len(walcl_series) >= lookback else walcl_series
        if window.iloc[-1] - window.iloc[0] > 0:
            score += thresholds["walcl_uptrend_bonus"]
    if hike_priced_pct is not None and hike_priced_pct > thresholds["hike_priced_threshold_pct"]:
        score -= thresholds["hike_priced_penalty"]
    return _clamp(score)


def score_s02_foreign_flow(ownership_zscore, usdkrw, thresholds):
    """ownership_zscore: manual z-score of KOSPI 외국인 보유비중 (낮을수록 headroom 높음)."""
    if ownership_zscore is None:
        return None
    z_low = thresholds["ownership_zscore_low"]
    score_at_low = thresholds["score_at_zscore_low"]
    neutral = 50
    slope = (score_at_low - neutral) / z_low if z_low else 0
    score = _clamp(neutral + slope * ownership_zscore)
    if usdkrw is not None and usdkrw > thresholds["usdkrw_gate_threshold"]:
        score *= thresholds["usdkrw_gate_multiplier"]
    return score


def score_s03_domestic_credit(credit_balance_krw, kospi_market_cap_krw, thresholds):
    if thresholds.get("forced_liquidation_event"):
        return min(15, thresholds["forced_liquidation_score_cap"])
    if not credit_balance_krw or not kospi_market_cap_krw:
        return None
    ratio_pct = credit_balance_krw / kospi_market_cap_krw * 100
    return _clamp(_linear_band(ratio_pct, thresholds["margin_ratio_low_pct"], thresholds["margin_ratio_high_pct"], 90, 10))


def score_s04_dry_powder(mmf_total_usd, real_rate_pct, thresholds):
    if mmf_total_usd is None:
        return None
    score = _linear_band(mmf_total_usd, thresholds["mmf_aum_low_usd"], thresholds["mmf_aum_high_usd"], 10, 90)
    if real_rate_pct is not None and real_rate_pct > 0:
        score -= real_rate_pct * thresholds["real_rate_penalty_per_pct"]
    return _clamp(score)


def score_s05_fx(usdkrw, thresholds):
    if usdkrw is None:
        return None
    return _clamp(_linear_band(
        usdkrw,
        thresholds["high_score_usdkrw_threshold"],
        thresholds["low_score_usdkrw_threshold"],
        thresholds["score_high"],
        thresholds["score_low"],
    ))


def score_s06_global_credit(hy_oas, vix, thresholds):
    if hy_oas is None or vix is None:
        return None
    oas_score = _linear_band(hy_oas, thresholds["hy_oas_tight_pct"], thresholds["hy_oas_wide_pct"], 90, 10)
    vix_score = _linear_band(vix, thresholds["vix_low"], thresholds["vix_high"], 90, 10)
    score = (oas_score + vix_score) / 2
    late_cycle = hy_oas >= thresholds["hy_oas_wide_pct"] and vix >= thresholds["vix_high"]
    if late_cycle:
        score = min(score, thresholds["late_cycle_score_cap"])
    return _clamp(score)


# ---- §4-2 합성 점수 → regime ----


def composite_score(subscores, weights):
    """subscores/weights: {"S01": value, ...}. Missing (None) subscores are excluded and
    the remaining weights are renormalized. Returns (score, n_available, n_total) or (None, 0, n_total)."""
    n_total = len(weights)
    available = {k: v for k, v in subscores.items() if v is not None}
    if not available:
        return None, 0, n_total
    total_weight = sum(weights[k] for k in available)
    if total_weight == 0:
        return None, 0, n_total
    score = sum(available[k] * weights[k] for k in available) / total_weight
    return score, len(available), n_total


def regime_from_score(score, regime_cuts):
    """regime_cuts: [low_cut, high_cut], e.g. [33, 66]."""
    if score is None:
        return None
    low, high = regime_cuts
    if score <= low:
        return "base"
    if score <= high:
        return "bull"
    return "hyper"


# ---- §4-3 정합성 (가격 밴드 vs 유동성이 허용하는 regime) ----

_BAND_RANK = {"base": 0, "bull": 1, "hyper": 2, "above_hyper": 3}


def liquidity_supported_ceiling(levels, regime):
    """levels: ceiling_levels() output. regime: 'base'|'bull'|'hyper'. Returns the upper bound of that band."""
    if levels is None or regime is None:
        return None
    return levels[regime][1]


def reconciliation_status(price_band, regime):
    """price_band: band_position()['band']. regime: 'base'|'bull'|'hyper' (max sustainable scenario).
    Returns 'aligned' | 'overheated' | 'slack' | None."""
    if price_band is None or regime is None:
        return None
    price_rank = _BAND_RANK[price_band]
    regime_rank = _BAND_RANK[regime]
    if price_rank == regime_rank:
        return "aligned"
    return "overheated" if price_rank > regime_rank else "slack"


# ---- §5 워치리스트 ----


def evaluate_watchlist(watchlist_items, ctx):
    """ctx supplies pre-resolved current values/series/thresholds (see app.py). Returns
    a list of watchlist dicts with an added 'status' key: 'fired' | 'quiet' | 'manual_check' | 'unknown'."""
    return [{**item, "status": _evaluate_trigger(item["id"], ctx)} for item in watchlist_items]


def _evaluate_trigger(trigger_id, ctx):
    if trigger_id == "fed_dot_plot":
        dot_cut = ctx.get("fed_dot_plot_2026_cut")
        walcl_dir = ctx.get("walcl_direction")
        if dot_cut is None and walcl_dir is None:
            return "unknown"
        return "fired" if (dot_cut or walcl_dir == "up") else "quiet"

    if trigger_id == "foreign_netsell_streak":
        series = ctx.get("foreign_netbuy_series")
        if series is None or len(series) < 3:
            return "unknown"
        return "fired" if (series.iloc[-3:] < 0).all() else "quiet"

    if trigger_id == "margin_forced_liquidation":
        event = ctx.get("forced_liquidation_event")
        return "fired" if event else "quiet"

    if trigger_id == "mmf_outflow":
        return "manual_check"

    if trigger_id == "usdkrw_gate":
        usdkrw = ctx.get("usdkrw")
        threshold = ctx.get("usdkrw_gate_threshold")
        if usdkrw is None or threshold is None:
            return "unknown"
        return "fired" if usdkrw < threshold else "quiet"

    if trigger_id == "credit_spread_vol":
        oas_dir = ctx.get("hy_oas_direction")
        vix_dir = ctx.get("vix_direction")
        if oas_dir is None or vix_dir is None:
            return "unknown"
        return "fired" if (oas_dir == "up" and vix_dir == "up") else "quiet"

    if trigger_id == "breadth_divergence":
        return "manual_check"

    return "unknown"


# ---- 섹터 트리맵 / RRG (Leadership layer) ----


def build_aggregate_series(series_list):
    """Equal-weighted average of constituent price series, each rebased to 100 at its
    first point. Used as a theme-sector proxy index when no single clean index/ETF
    exists (e.g. KOSPI investment-theme groupings). Returns None if nothing usable."""
    normalized = [s / s.iloc[0] * 100 for s in series_list if s is not None and not s.empty]
    if not normalized:
        return None
    aligned = pd.concat(normalized, axis=1, join="inner")
    if aligned.empty:
        return None
    return aligned.mean(axis=1)


def compute_rs_ratio_momentum(target_series, benchmark_series, ratio_window=10, momentum_window=10):
    """Simplified RRG calc (JdK-style approximation): RS-Ratio is the target/benchmark
    relative-strength line normalized to its own rolling mean (centered at 100);
    RS-Momentum is the rate of change of RS-Ratio (also centered at 100).
    Returns (rs_ratio, rs_momentum), either None if there isn't enough overlapping history."""
    if target_series is None or benchmark_series is None:
        return None, None
    aligned = pd.concat([target_series, benchmark_series], axis=1, join="inner").dropna()
    if len(aligned) < ratio_window + momentum_window + 1:
        return None, None
    relative = aligned.iloc[:, 0] / aligned.iloc[:, 1]
    rs_ratio_series = (100 * relative / relative.rolling(ratio_window).mean()).dropna()
    if len(rs_ratio_series) < momentum_window + 1:
        return None, None
    rs_momentum_series = (100 * rs_ratio_series / rs_ratio_series.shift(momentum_window)).dropna()
    if rs_ratio_series.empty or rs_momentum_series.empty:
        return None, None
    return float(rs_ratio_series.iloc[-1]), float(rs_momentum_series.iloc[-1])


def rrg_quadrant(rs_ratio, rs_momentum):
    """Returns 'leading' | 'weakening' | 'improving' | 'lagging' | None. Centered at 100."""
    if rs_ratio is None or rs_momentum is None:
        return None
    if rs_ratio >= 100:
        return "leading" if rs_momentum >= 100 else "weakening"
    return "improving" if rs_momentum >= 100 else "lagging"


QUADRANT_LABEL = {"leading": "주도 지속", "weakening": "차익 임박", "improving": "순환매 진입", "lagging": "소외"}
QUADRANT_COLOR = {
    "leading": "rgba(95,185,142,0.85)",
    "weakening": "rgba(208,107,74,0.85)",
    "improving": "rgba(205,177,90,0.85)",
    "lagging": "rgba(127,147,196,0.85)",
}


def sector_weight_pct(constituent_market_caps, total_market_cap):
    caps = [c for c in constituent_market_caps if c]
    if not caps or not total_market_cap:
        return None
    return sum(caps) / total_market_cap * 100


def realized_volatility(series, window=20):
    """Annualized realized volatility (%) from trailing daily returns — a free, computable
    approximation for markets without a quoted implied-vol index (e.g. no free VKOSPI)."""
    if series is None or len(series) < window + 1:
        return None
    returns = series.pct_change().dropna()
    recent = returns.iloc[-window:]
    if len(recent) < 2:
        return None
    return float(recent.std() * (252 ** 0.5) * 100)
