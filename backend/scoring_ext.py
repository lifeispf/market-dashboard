"""§13-1 Fear & Greed — independent psychology/positioning gauge.

Deliberately separate from scoring.py's REGIME (S01-S06): REGIME measures objective
liquidity fuel, fear_greed measures short-horizon crowd psychology. They are NEVER
summed together (per planning/archaive/기획안_expension_spec.md §13-0 "절대 섞지 않는다").

MVP scope (4 factors, all already-available data, no new auth wall):
  F1 momentum  — price / 125d SMA - 1            (above MA = greed)
  F2 breadth   — advancers / (advancers+decliners) or sector-up-ratio for NASDAQ
                 (KOSPI breadth needs KRX auth -> degrades to 3 factors without it)
  F3 vol       — VIX / VKOSPI-approx, inverted    (low vol = greed)
  F4 credit    — HY OAS spread, inverted          (tight spread = greed)

F5 (safe-haven) / F6 (put/call) are spec'd for a later expansion and intentionally
not implemented here (data wall risk per spec §13-1) — fear_greed() simply omits
them from `factors` and renormalizes over whatever subset is available, exactly like
scoring.composite_score() does for S01-S06.
"""
from scoring import _clamp, _linear_band

FACTOR_NAMES = {
    "F1": "모멘텀",
    "F2": "강도",
    "F3": "변동성",
    "F4": "신용",
}

LABEL_BANDS = [
    (24, "Extreme Fear"),
    (44, "Fear"),
    (55, "Neutral"),
    (74, "Greed"),
    (None, "Extreme Greed"),
]


def _score_momentum(price, sma, anchors):
    """F1: (price/sma - 1) * 100 -> 0..100, lo_pct=fear anchor, hi_pct=greed anchor."""
    if price is None or sma is None or not sma:
        return None, None
    value = (price / sma - 1) * 100
    score = _clamp(_linear_band(value, anchors["lo_pct"], anchors["hi_pct"], 0, 100))
    return value, score


def _score_breadth(up_ratio, anchors):
    """F2: up_ratio is advancers/(advancers+decliners) in [0,1], or sector-up-ratio."""
    if up_ratio is None:
        return None, None
    score = _clamp(_linear_band(up_ratio, anchors["lo"], anchors["hi"], 0, 100))
    return up_ratio, score


def _score_inverted(value, anchors, key_lo="lo", key_hi="hi"):
    """Shared shape for F3 (vol) / F4 (oas): low raw value -> greed (100), so the
    linear band is built hi->lo explicitly rather than relying on a generic 'invert'
    flag, keeping this function the single place the inversion direction is decided."""
    if value is None:
        return None, None
    lo, hi = anchors[key_lo], anchors[key_hi]
    score = _clamp(_linear_band(value, lo, hi, 100, 0))
    return value, score


def _label_for(score, cuts):
    """cuts: 4 ascending boundaries, e.g. [25, 45, 56, 75] (lower-bound inclusive of each
    band per spec: 0-24 / 25-44 / 45-55 / 56-74 / 75-100)."""
    if score is None:
        return "N/A"
    c1, c2, c3, c4 = cuts
    if score < c1:
        return "Extreme Fear"
    if score < c2:
        return "Fear"
    if score < c3:
        return "Neutral"
    if score < c4:
        return "Greed"
    return "Extreme Greed"


def fear_greed(price, sma_125, up_ratio, vix_or_vkospi, hy_oas, fg_config):
    """Computes the §13-1 MVP (F1-F4) fear&greed gauge.

    Args:
        price: current index level, or None.
        sma_125: 125-day simple moving average of the index, or None.
        up_ratio: advancers/(advancers+decliners) in [0,1] (KOSPI) or sector-up-ratio
            in [0,1] (NASDAQ proxy), or None if unavailable (e.g. KOSPI w/o KRX auth).
        vix_or_vkospi: VIX value (NASDAQ) or realized-vol approx (KOSPI), or None.
        hy_oas: HY OAS spread (%), or None.
        fg_config: config["fear_greed"] block -- {"weights": {...}, "cuts": [...],
            "anchors": {...}}.

    Returns: {"score", "label", "nAvailable", "nTotal", "factors": [...]} -- matches
    the frozen FearGreed contract shape exactly. Never raises; all-None inputs yield
    score=None, label="N/A", nAvailable=0, factors=[] (every factor entry omitted, not
    null-padded -- consistent with contract.md's "leaders 없는 섹터는 키 자체 생략 가능"
    spirit of omitting rather than null-filling absent structure).
    """
    weights = fg_config["weights"]
    anchors = fg_config["anchors"]
    cuts = fg_config["cuts"]
    n_total = len(weights)

    raw = {
        "F1": _score_momentum(price, sma_125, anchors["F1_momentum"]),
        "F2": _score_breadth(up_ratio, anchors["F2_breadth"]),
        "F3": _score_inverted(vix_or_vkospi, anchors["F3_vol"], "lo", "hi"),
        "F4": _score_inverted(hy_oas, anchors["F4_oas"], "lo_pct", "hi_pct"),
    }

    factors = []
    available = {}
    for fid, (value, score) in raw.items():
        if score is not None:
            available[fid] = score
        # Only emit a factor entry when we actually attempted to compute it (i.e. it's
        # in the MVP weight set) -- F5/F6 stay fully absent until implemented.
        if fid in weights:
            factors.append({"id": fid, "name": FACTOR_NAMES[fid], "value": value, "score": score})

    if not available:
        return {"score": None, "label": "N/A", "nAvailable": 0, "nTotal": n_total, "factors": factors}

    total_weight = sum(weights[fid] for fid in available if fid in weights)
    if total_weight == 0:
        return {"score": None, "label": "N/A", "nAvailable": 0, "nTotal": n_total, "factors": factors}

    composite = sum(available[fid] * weights[fid] for fid in available if fid in weights) / total_weight
    composite = _clamp(composite)
    label = _label_for(composite, cuts)

    return {
        "score": composite,
        "label": label,
        "nAvailable": len(available),
        "nTotal": n_total,
        "factors": factors,
    }
