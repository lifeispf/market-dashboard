"""engine/verification/scorecard.py — Phase F 검증 스코어카드 (v1).

"모든 신호가 비검증"인 상태를 실측 신뢰도로 바꾸기 위한 첫 단계. 백필된
series_daily(5년 일봉)에서 백테스트 가능한 부분집합을 과거 시점마다 재구성하고
**forward-return과 상관**시킨다. look-ahead 금지: signal(t)는 항상 미래
수익(t→t+h)과만 비교한다. 모든 지표에 표본수 n을 보고하고, 백테스트 불가
항목(manual/KRX)은 명시적으로 제외한다.

정본: planning/elegant-soaring-twilight.md Phase F. scoring.py/scoring_ext.py는
호출/공식 미러만 하고 수정하지 않는다(보호 파일). 풀 walk-forward(롤링
in/out-of-sample)는 v2로 분리 — 여기서는 전구간 IC/hit-rate 스코어카드다.
"""
from __future__ import annotations

import pandas as pd

import scoring
from backend import scoring_ext
from backend.store import db, series_map
from config_loader import load_config, load_sectors

# horizons in trading days
_H_SHORT = 21   # ~1M
_H_LONG = 63    # ~3M
_MIN_N = 10     # below this, an IC/stat is too thin to report
_RRG_W = 10     # mirrors config["rrg"] ratio/momentum window (scoring default)


def _series(series_id: str) -> "pd.Series | None":
    """series_daily 한 시리즈를 날짜 인덱스 pandas Series로. 없으면 None."""
    rows = db.read_series(series_id)
    if not rows:
        return None
    idx = pd.to_datetime([d for d, _ in rows])
    s = pd.Series([float(v) for _, v in rows], index=idx).sort_index()
    return s[~s.index.duplicated(keep="last")]


def _forward_return(level: "pd.Series", h: int) -> "pd.Series":
    """t→t+h 미래 수익률. shift(-h)이므로 look-ahead 없음(미래값을 t에 귀속만)."""
    return level.shift(-h) / level - 1.0


def _spearman_ic(signal: "pd.Series", fwd: "pd.Series") -> tuple:
    """signal(t) vs forward-return(t)의 Spearman IC + 표본수. 정렬·dropna 후 계산.

    Spearman = 순위(rank)에 대한 Pearson 상관. pandas의 method="spearman"은 내부적으로
    scipy를 import하는데 이 venv엔 scipy가 없으므로(numpy/pandas만), rank() 후 기본
    Pearson corr(numpy 기반)로 동일 결과를 낸다 — 외부 의존 없음.
    """
    df = pd.concat([signal, fwd], axis=1, join="inner").dropna()
    if len(df) < _MIN_N:
        return None, len(df)
    ic = df.iloc[:, 0].rank().corr(df.iloc[:, 1].rank())
    return (round(float(ic), 4) if pd.notna(ic) else None), int(len(df))


# --------------------------------------------------------------------------
# (a) Fear & Greed 극단 → 반전(contrarian) 검증
# --------------------------------------------------------------------------
def _fear_greed_series(market: str, level: "pd.Series", config: dict) -> "pd.Series":
    """일별 F&G 합성 점수 series 재구성(backend/api/history.py Phase B와 동일 방식).

    breadth(F2)는 과거 미저장 → up_ratio=None으로 degrade(라이브 KOSPI-무KRX와 동일).
    vol은 NASDAQ=fred:vix, KOSPI=실현변동성 근사. 날짜 미스매치는 ffill as-of.
    """
    fg_cfg = config["fear_greed"]
    sma125 = level.rolling(125).mean()
    if market == "NASDAQ":
        vix = _series("fred:vix")
        vol = vix.reindex(level.index, method="ffill") if vix is not None else None
    else:
        vol = level.pct_change().rolling(20).std() * (252 ** 0.5) * 100
    oas = _series("fred:hy_oas")
    oas_a = oas.reindex(level.index, method="ffill") if oas is not None else None

    out = {}
    for t in level.index:
        price = level.loc[t]
        sma = sma125.loc[t]
        v = vol.loc[t] if (vol is not None and t in vol.index) else None
        o = oas_a.loc[t] if (oas_a is not None and t in oas_a.index) else None
        fg = scoring_ext.fear_greed(
            price=float(price) if pd.notna(price) else None,
            sma_125=float(sma) if pd.notna(sma) else None,
            up_ratio=None,
            vix_or_vkospi=float(v) if (v is not None and pd.notna(v)) else None,
            hy_oas=float(o) if (o is not None and pd.notna(o)) else None,
            fg_config=fg_cfg,
        )
        out[t] = fg.get("score")
    return pd.Series(out)


def _fear_greed_extremes(market: str, level: "pd.Series", config: dict) -> dict:
    fg = _fear_greed_series(market, level, config)
    res = {}
    for h in (_H_SHORT, _H_LONG):
        fwd = _forward_return(level, h)
        df = pd.concat([fg.rename("fg"), fwd.rename("fwd")], axis=1, join="inner").dropna()
        greed = df[df["fg"] >= 75]["fwd"]
        fear = df[df["fg"] <= 25]["fwd"]
        res[str(h)] = {
            "greed": {
                "mean_fwd_ret_pct": round(float(greed.mean()) * 100, 2) if len(greed) else None,
                "pct_negative": round(float((greed < 0).mean()) * 100, 1) if len(greed) else None,
                "n": int(len(greed)),
            },
            "fear": {
                "mean_fwd_ret_pct": round(float(fear.mean()) * 100, 2) if len(fear) else None,
                "pct_positive": round(float((fear > 0).mean()) * 100, 1) if len(fear) else None,
                "n": int(len(fear)),
            },
        }
    return res


# --------------------------------------------------------------------------
# (b) 섹터 RRG quadrant → 섹터 초과수익 hit-rate
# --------------------------------------------------------------------------
def _rs_quadrant_series(sector: "pd.Series", benchmark: "pd.Series") -> "pd.Series":
    """RS-Ratio/Momentum series에서 quadrant series. scoring.compute_rs_ratio_momentum의
    공식을 그대로 미러(그 함수는 마지막 점만 반환하므로 series용으로 재현):
        relative = sector/benchmark
        rs_ratio = 100 * relative / relative.rolling(W).mean()
        rs_momentum = 100 * rs_ratio / rs_ratio.shift(W)
    quadrant 경계는 scoring.rrg_quadrant와 동일(100 중심)."""
    aligned = pd.concat([sector, benchmark], axis=1, join="inner").dropna()
    if len(aligned) < _RRG_W * 2 + 2:
        return pd.Series(dtype=object)
    relative = aligned.iloc[:, 0] / aligned.iloc[:, 1]
    rs_ratio = 100 * relative / relative.rolling(_RRG_W).mean()
    rs_mom = 100 * rs_ratio / rs_ratio.shift(_RRG_W)
    q = pd.Series(index=rs_ratio.index, dtype=object)
    # mirrors scoring.rrg_quadrant exactly
    lead = (rs_ratio >= 100) & (rs_mom >= 100)
    weak = (rs_ratio >= 100) & (rs_mom < 100)
    impr = (rs_ratio < 100) & (rs_mom >= 100)
    lagg = (rs_ratio < 100) & (rs_mom < 100)
    q[lead] = "leading"; q[weak] = "weakening"; q[impr] = "improving"; q[lagg] = "lagging"
    q[rs_ratio.isna() | rs_mom.isna()] = None
    return q


def _sector_rrg_hit_rate(market: str, level: "pd.Series", h: int = _H_SHORT) -> dict:
    from engine.sector.inputs import build_sector_price_series  # local: avoid cycle at import
    registry = series_map.build_registry(market, load_sectors())
    sector_defs = load_sectors()[market]["sectors"]
    bull_hits, bull_n, bear_hits, bear_n = 0, 0, 0, 0
    bench_fwd = _forward_return(level, h)
    for sdef in sector_defs.values():
        sec = build_sector_price_series(sdef, registry, tf="1Y")
        if sec is None:
            continue
        sec = sec[~sec.index.duplicated(keep="last")].sort_index()
        q = _rs_quadrant_series(sec, level)
        if q.empty:
            continue
        sec_fwd = _forward_return(sec, h)
        # excess = sector forward return - index forward return (aligned dates)
        df = pd.concat([q.rename("q"), sec_fwd.rename("s"), bench_fwd.rename("b")], axis=1, join="inner").dropna(subset=["s", "b"])
        df = df[df["q"].notna()]
        if df.empty:
            continue
        excess = df["s"] - df["b"]
        bull = df["q"].isin(["leading", "improving"])
        bear = df["q"].isin(["lagging", "weakening"])
        bull_hits += int((excess[bull] > 0).sum()); bull_n += int(bull.sum())
        bear_hits += int((excess[bear] < 0).sum()); bear_n += int(bear.sum())
    return {
        "horizon_days": h,
        "hit_rate_bullish": round(bull_hits / bull_n * 100, 1) if bull_n else None,
        "n_bullish": bull_n,
        "hit_rate_bearish": round(bear_hits / bear_n * 100, 1) if bear_n else None,
        "n_bearish": bear_n,
    }


# --------------------------------------------------------------------------
# (c) 모멘텀 IC (baseline sanity)
# --------------------------------------------------------------------------
def _momentum_ic(level: "pd.Series") -> dict:
    mom = level / level.shift(_H_LONG) - 1.0          # 63d trailing return @t
    fwd = _forward_return(level, _H_SHORT)            # forward 21d return @t
    ic, n = _spearman_ic(mom, fwd)
    return {"ic": ic, "n": n, "desc": "지수 63일 추세수익 vs 향후 21일 수익(Spearman)"}


# --------------------------------------------------------------------------
# (d) Regime 팩터 IC (FRED 백테스트 부분집합) → F-④ 가중치 제안
# --------------------------------------------------------------------------
def _regime_factor_ic(market: str, level: "pd.Series", config: dict) -> dict:
    TH = config["thresholds"]
    fwd = _forward_return(level, _H_SHORT)

    # S05 (usd/krw) — scalar per date
    fx = _series("fred:usdkrw")
    s05 = fx.map(lambda x: scoring.score_s05_fx(float(x), TH["S05_fx_KRW"])) if fx is not None else None

    # S06 (vix·oas) — needs both per date
    vix = _series("fred:vix"); oas = _series("fred:hy_oas")
    s06 = None
    if vix is not None and oas is not None:
        both = pd.concat([oas.rename("o"), vix.rename("v")], axis=1, join="inner").dropna()
        s06 = both.apply(lambda r: scoring.score_s06_global_credit(float(r["o"]), float(r["v"]), TH["S06_global_credit"]), axis=1)

    # S01 (WALCL trend) — fn takes a SERIES (trailing trend); compute per walcl date on expanding slice
    walcl = _series("fred:fed_balance_sheet")
    s01 = None
    if walcl is not None and len(walcl) >= 2:
        vals = {}
        for i in range(2, len(walcl) + 1):
            t = walcl.index[i - 1]
            vals[t] = scoring.score_s01_central_bank(walcl.iloc[:i], None, None, TH["S01_central_bank"])
        s01 = pd.Series(vals)

    factors = {}
    for key, ser in (("S01", s01), ("S05", s05), ("S06", s06)):
        if ser is None:
            factors[key] = {"ic": None, "n": 0}
            continue
        ser = ser.reindex(level.index, method="ffill")
        ic, n = _spearman_ic(ser, fwd)
        factors[key] = {"ic": ic, "n": n}

    # IC-proportional suggested weights over the positive-IC subset; current = config renormalized over {S01,S05,S06}
    w = config["weights"][market]
    subset = ["S01", "S05", "S06"]
    cur_total = sum(w[k] for k in subset) or 1.0
    current_weights = {k: round(w[k] / cur_total, 3) for k in subset}
    pos = {k: factors[k]["ic"] for k in subset if factors[k]["ic"] and factors[k]["ic"] > 0}
    pos_total = sum(pos.values())
    suggested = {k: (round(pos[k] / pos_total, 3) if k in pos else 0.0) for k in subset} if pos_total > 0 else None

    return {
        "factors": factors,
        "current_weights_subset": current_weights,
        "suggested_weights_subset": suggested,
        "note": "FRED 백테스트 부분집합(S01·S05·S06)만 — S02/S03/S04는 과거 데이터 부재로 제외. "
                "IC>0 팩터에 비례한 제안치이며 자동 적용하지 않음(검증 게이트·config 보호).",
    }


# --------------------------------------------------------------------------
def build_scorecard(market: str) -> dict:
    """market의 검증 스코어카드. 각 섹션은 독립적으로 try/except — 한 섹션
    실패가 전체를 무너뜨리지 않는다(never raise)."""
    config = load_config()
    level = _series(series_map.index_series_id(market))

    sections = {}
    if level is None or len(level) < _H_LONG + _MIN_N:
        sections["data_warning"] = f"지수 시리즈 부족(n={0 if level is None else len(level)}) — 백필 필요"
        level = level if level is not None else pd.Series(dtype=float)

    def _safe(name, fn):
        try:
            sections[name] = fn()
        except Exception as exc:  # noqa: BLE001 — 섹션 격리
            sections[name] = {"error": str(exc)}

    if len(level) >= _H_LONG + _MIN_N:
        _safe("fear_greed_extremes", lambda: _fear_greed_extremes(market, level, config))
        _safe("sector_rrg_hit_rate", lambda: _sector_rrg_hit_rate(market, level))
        _safe("momentum_ic", lambda: _momentum_ic(level))
        _safe("regime_factor_ic", lambda: _regime_factor_ic(market, level, config))

    sections["limitations"] = (
        "manual/KRX 팩터(S02 외국인·S03 신용·S04 MMF)는 과거 시계열 부재로 백테스트 제외. "
        "F&G의 F2(breadth)는 과거 미저장 → 가용 팩터로 재정규화(라이브와 동일 degrade). "
        "RRG는 단일 윈도우(10) 근사. 장기 호라이즌일수록 표본수 n이 작다 — n을 함께 볼 것. "
        "전구간 IC/hit-rate이며 롤링 walk-forward(out-of-sample 분리)는 v2."
    )
    sections["index_sample_n"] = int(len(level))
    return sections
