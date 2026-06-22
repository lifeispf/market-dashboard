from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

import scoring
from config_loader import load_config, load_sectors
from data import fred_fetcher, kr_fetcher, leadership_fetcher, manual, us_fetcher

st.set_page_config(page_title="유동성 천장 모니터링", layout="wide")

config = load_config()
sectors_config = load_sectors()

BAND_LABEL = {"base": "BASE", "bull": "BULL", "hyper": "HYPER", "above_hyper": "HYPER 초과"}
BAND_COLOR = {
    "base": "rgba(46,160,67,0.30)",
    "bull": "rgba(210,153,34,0.30)",
    "hyper": "rgba(218,54,51,0.30)",
}


@st.cache_data(ttl=3600)
def cached_kospi_level():
    return kr_fetcher.fetch_kospi_level()


@st.cache_data(ttl=3600)
def cached_us_price(name):
    return us_fetcher.fetch_last_price(name)


@st.cache_data(ttl=3600)
def cached_fred(name):
    return fred_fetcher.latest_value(name)


@st.cache_data(ttl=3600)
def cached_fred_series(name, lookback_days=400):
    return fred_fetcher.fetch_series(name, lookback_days=lookback_days)


@st.cache_data(ttl=3600)
def cached_foreign_netbuy(lookback_days=20):
    return kr_fetcher.fetch_foreign_institutional_netbuy(lookback_days)


@st.cache_data(ttl=3600)
def cached_breadth():
    return kr_fetcher.fetch_breadth()


@st.cache_data(ttl=3600)
def cached_kospi_market_cap():
    return kr_fetcher.fetch_kospi_total_market_cap()


@st.cache_data(ttl=3600)
def cached_kospi_fundamental():
    return kr_fetcher.fetch_kospi_fundamental()


@st.cache_data(ttl=3600)
def cached_kospi_level_series(lookback_days=365):
    return kr_fetcher.fetch_kospi_level_series(lookback_days)


@st.cache_data(ttl=3600)
def cached_us_price_series(name, period="1y"):
    return us_fetcher.fetch_price_series(name, period)


@st.cache_data(ttl=3600)
def cached_ticker_series(ticker, period="ytd"):
    return leadership_fetcher.fetch_ticker_series(ticker, period)


@st.cache_data(ttl=3600)
def cached_ticker_quote(ticker):
    return leadership_fetcher.fetch_ticker_quote(ticker)


def render_sparkline(series):
    fig = go.Figure(go.Scatter(x=list(range(len(series))), y=series.values, mode="lines", line=dict(width=2)))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(height=60, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    return fig


def render_source_card(col, code, title, value_text, sub_caption, series, direction, score=None):
    with col:
        arrow = scoring.DIRECTION_ARROW.get(direction, "")
        st.markdown(f"**{code} {title}** {arrow}")
        st.markdown(f"#### {value_text}")
        st.caption(sub_caption)
        if series is not None and len(series) >= 2:
            st.plotly_chart(render_sparkline(series), width="stretch", config={"displayModeBar": False})
        if score is not None:
            st.progress(int(round(score)))
            st.caption(f"여력 점수: {score:.0f}/100")
        else:
            st.caption("여력 점수: 입력값 부족")


st.title("유동성 천장 모니터링 대시보드")
market = st.radio("시장", ["KOSPI", "NASDAQ"], horizontal=True, label_visibility="collapsed")
narrative_slot = st.empty()

if market == "KOSPI":
    level, as_of, source, fetch_error = cached_kospi_level()
    eps_key = "KOSPI_forward_eps"
    anchors = config["multiple_anchors"]["KOSPI"]
else:
    level, as_of, fetch_error = cached_us_price("nasdaq_composite")
    source = "Yahoo Finance"
    eps_key = "NASDAQ_forward_eps"
    anchors = config["multiple_anchors"]["NASDAQ"]

forward_eps, eps_as_of, eps_missing = manual.get_override(config, eps_key)

position = scoring.band_position(level, forward_eps, anchors) if level is not None else None

# ---- Flow 레이어 데이터 (1일%/YoY%/trailing PER/breadth/vol) ----
if market == "KOSPI":
    flow_series, flow_source, flow_err = cached_kospi_level_series(365)
else:
    flow_series, flow_err = cached_us_price_series("nasdaq_composite", "1y")
    flow_source = "Yahoo Finance"

chg_1d_pct = None
yoy_pct = None
if flow_series is not None and len(flow_series) >= 2:
    chg_1d_pct = (flow_series.iloc[-1] / flow_series.iloc[-2] - 1) * 100
    yoy_pct = (flow_series.iloc[-1] / flow_series.iloc[0] - 1) * 100

if market == "KOSPI":
    trailing_per, kospi_forward_per_xcheck, fundamental_as_of, fundamental_err = cached_kospi_fundamental()
    advancers, decliners, breadth_as_of, breadth_err = cached_breadth()
    breadth_text = f"상승 {advancers} · 하락 {decliners}" if advancers is not None else None
    vol_label, vol_value = "VKOSPI(근사·실현변동성)", scoring.realized_volatility(flow_series, window=20)
else:
    trailing_per, kospi_forward_per_xcheck, fundamental_err = None, None, "NASDAQ 종합 trailing PER 소스 없음"
    nasdaq_sectors = sectors_config["NASDAQ"]["sectors"]
    sector_ups = sector_downs = 0
    for sdef in nasdaq_sectors.values():
        etf_series, _ = cached_ticker_series(sdef["etf"], "5d")
        if etf_series is not None and len(etf_series) >= 2:
            if etf_series.iloc[-1] > etf_series.iloc[-2]:
                sector_ups += 1
            elif etf_series.iloc[-1] < etf_series.iloc[-2]:
                sector_downs += 1
    breadth_text = f"섹터 {sector_ups}개 상승 · {sector_downs}개 하락"
    vol_label = "VIX"
    vol_value, _, _ = cached_fred("vix")

# ---- A. KPI 헤더 ----
fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)

with fcol1:
    if level is not None:
        st.metric(f"{market} 현재", f"{level:,.2f}", f"{chg_1d_pct:+.2f}% (1D)" if chg_1d_pct is not None else None)
        st.caption(f"출처: {source} · {as_of}")
    else:
        st.metric(f"{market} 현재", "N/A")
        st.caption(f"⚠ 조회 실패: {fetch_error}")

with fcol2:
    st.metric("YoY", f"{yoy_pct:+.0f}%" if yoy_pct is not None else "N/A")
    st.caption(f"출처: {flow_source}" if yoy_pct is not None else f"⚠ {flow_err}")

with fcol3:
    if forward_eps and level is not None:
        mult = scoring.current_multiple(level, forward_eps)
        st.metric("선행 PER", f"{mult:.1f}x")
    else:
        st.metric("선행 PER", "EPS 입력 필요")
    st.caption(f"trailing {trailing_per:.1f}x" if trailing_per is not None else f"trailing N/A ({fundamental_err})")

with fcol4:
    st.metric("Breadth", breadth_text or "N/A")
    if market == "KOSPI" and breadth_text is None:
        st.caption(f"⚠ {breadth_err}")

with fcol5:
    st.metric(vol_label, f"{vol_value:.1f}" if vol_value is not None else "N/A")

if market == "KOSPI" and kospi_forward_per_xcheck:
    st.caption(f"참고 · KRX 선행PER(자체 컨센서스) {kospi_forward_per_xcheck:.1f}x — manual_overrides 입력값과 비교용, 0으로 비어있으면 표시 안 됨")

if flow_series is not None and len(flow_series) >= 5:
    st.plotly_chart(render_sparkline(flow_series.iloc[-60:]), width="stretch", config={"displayModeBar": False})

st.divider()

bcol1, bcol2 = st.columns(2)
with bcol1:
    st.metric("현재 밴드", BAND_LABEL[position["band"]] if position else "N/A")
with bcol2:
    st.metric("천장까지 여유", f"{position['distance_pct']:+.1f}%" if position else "N/A")
if forward_eps and level is not None:
    caption = f"선행EPS {forward_eps:,.0f}"
    if eps_as_of:
        caption += f" (입력일 {eps_as_of})"
    st.caption(caption)
else:
    st.caption(f"config.json manual_overrides.{eps_key} 에 입력하면 선행 PER·밴드가 표시됩니다.")

st.divider()

# ---- B. 천장 밴드 차트 ----
st.subheader("천장 밴드")

levels = scoring.ceiling_levels(forward_eps, anchors)
if levels is None:
    st.info(f"{eps_key} 값을 config.json의 manual_overrides에 입력하면 밴드가 표시됩니다.")
else:
    fig = go.Figure()
    for scenario in scoring.BAND_ORDER:
        lo, hi = levels[scenario]
        fig.add_hrect(
            y0=lo,
            y1=hi,
            fillcolor=BAND_COLOR[scenario],
            line_width=0,
            annotation_text=f"{scenario.upper()}  {lo:,.0f}–{hi:,.0f}",
            annotation_position="top left",
        )
    if level is not None:
        fig.add_hline(
            y=level,
            line_dash="dot",
            line_color="white",
            line_width=2,
            annotation_text=f"현재 {level:,.0f}",
            annotation_position="right",
        )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(title="지수 레벨")
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")

st.divider()

# ---- 원천 raw 데이터 수집 (S01-S06 공통, 시장과 무관) ----
walcl, walcl_err = cached_fred_series("fed_balance_sheet", lookback_days=180)
fed_dot_plot_2026_cut, dot_plot_as_of, _ = manual.get_override(config, "fed_dot_plot_2026_cut")
fed_hike_priced_pct, hike_priced_as_of, _ = manual.get_override(config, "fed_hike_priced_pct")

netbuy_df, netbuy_err = cached_foreign_netbuy(20)
foreign_series = netbuy_df["외국인합계"] if netbuy_df is not None and "외국인합계" in (netbuy_df.columns if netbuy_df is not None else []) else None
foreign_ownership_zscore, ownership_zscore_as_of, _ = manual.get_override(config, "foreign_ownership_zscore")

credit_value, credit_as_of, credit_missing = manual.get_override(config, "credit_balance_krw")
market_cap, market_cap_as_of, market_cap_err = cached_kospi_market_cap()
if market_cap is None:
    market_cap, _, _ = manual.get_override(config, "kospi_total_market_cap_krw")

mmf_value, mmf_as_of, mmf_missing = manual.get_override(config, "mmf_total_usd")
real_rate, real_rate_as_of, real_rate_err = cached_fred("real_rate_2y")

fx_series, fx_err = cached_fred_series("usdkrw", lookback_days=90)
usdkrw = fx_series.iloc[-1] if fx_series is not None and not fx_series.empty else None

oas_series, oas_err = cached_fred_series("hy_oas", lookback_days=180)
vix_series, vix_err = cached_fred_series("vix", lookback_days=30)
hy_oas = oas_series.iloc[-1] if oas_series is not None and not oas_series.empty else None
vix_value = vix_series.iloc[-1] if vix_series is not None and not vix_series.empty else None

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
vix_dir = scoring.trend_direction(vix_series, lookback=5) if vix_series is not None else None

# ---- E. 6개 원천 패널 ----
st.subheader("6개 원천 패널")
st.caption("두 시장 모두 동일한 6원천을 공유하며, 시장별 가중치 차이는 합성점수 단계에서 적용됩니다.")

row1 = st.columns(3)
row2 = st.columns(3)

s01_value = f"${walcl.iloc[-1] / 1e6:.2f}T" if walcl is not None and not walcl.empty else "N/A"
s01_sub = f"WALCL · {walcl.index[-1].date()}" if walcl is not None and not walcl.empty else f"⚠ {walcl_err}"
render_source_card(row1[0], "S01", "중앙은행", s01_value, s01_sub, walcl, s01_dir, s01_score)

if foreign_series is not None:
    s02_value = f"{foreign_series.iloc[-1] / 1e8:,.0f}억"
    s02_sub = f"외국인 순매수(KOSPI) · {foreign_series.index[-1]}"
else:
    s02_value, s02_sub = "N/A", f"⚠ {netbuy_err}"
render_source_card(row1[1], "S02", "외국인(KR)", s02_value, s02_sub, foreign_series, s02_dir, s02_score)

if not credit_missing:
    s03_value = f"{credit_value / 1e12:,.1f}조"
    stale = manual.staleness_level(credit_as_of, "daily", config)
    s03_sub = f"수동입력 · {credit_as_of} ({stale})"
else:
    s03_value, s03_sub = "미입력", "config.json manual_overrides.credit_balance_krw"
render_source_card(row1[2], "S03", "신용잔고(KR)", s03_value, s03_sub, None, None, s03_score)

if not mmf_missing:
    s04_value = f"${mmf_value / 1e12:,.2f}T"
    stale = manual.staleness_level(mmf_as_of, "weekly", config)
    s04_sub = f"수동입력 · {mmf_as_of} ({stale})"
else:
    s04_value, s04_sub = "미입력", "config.json manual_overrides.mmf_total_usd"
render_source_card(row2[0], "S04", "대기자금(US)", s04_value, s04_sub, None, None, s04_score)

s05_value = f"{usdkrw:,.1f}" if usdkrw is not None else "N/A"
s05_sub = f"USD/KRW · {fx_series.index[-1].date()}" if fx_series is not None and not fx_series.empty else f"⚠ {fx_err}"
render_source_card(row2[1], "S05", "환율", s05_value, s05_sub, fx_series, s05_dir, s05_score)

s06_value = f"{hy_oas:.2f}%" if hy_oas is not None else "N/A"
s06_sub = "HY OAS" + (f" · VIX {vix_value:.1f}" if vix_value is not None else " · VIX N/A") if hy_oas is not None else f"⚠ {oas_err}"
render_source_card(row2[2], "S06", "글로벌신용", s06_value, s06_sub, oas_series, s06_dir, s06_score)

st.divider()

# ---- C. 유동성 REGIME 게이지 ----
st.subheader("유동성 REGIME 게이지")

weights = config["weights"][market]
subscores = {"S01": s01_score, "S02": s02_score, "S03": s03_score, "S04": s04_score, "S05": s05_score, "S06": s06_score}
composite, n_avail, n_total = scoring.composite_score(subscores, weights)
regime = scoring.regime_from_score(composite, config["regime_cuts"])

REGIME_LABEL = {
    "base": "BASE only — 멀티플 유지가 한계",
    "bull": "BULL 도달가능 — 재평가 연료 부분충전",
    "hyper": "HYPER 연료 존재 — 지속가능성은 별도 경고",
}

gcol1, gcol2 = st.columns([2, 1])
with gcol1:
    if composite is not None:
        low_cut, high_cut = config["regime_cuts"]
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=composite,
            number={"suffix": "/100"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "white"},
                "steps": [
                    {"range": [0, low_cut], "color": BAND_COLOR["base"]},
                    {"range": [low_cut, high_cut], "color": BAND_COLOR["bull"]},
                    {"range": [high_cut, 100], "color": BAND_COLOR["hyper"]},
                ],
            },
        ))
        fig.update_layout(height=220, margin=dict(l=20, r=20, t=20, b=10))
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("서브점수가 전부 없어 합성점수를 계산할 수 없습니다 (manual_overrides 입력 필요).")
with gcol2:
    st.metric(f"{market} Regime", regime.upper() if regime else "N/A")
    if regime:
        st.caption(REGIME_LABEL[regime])
    st.caption(f"반영된 원천: {n_avail}/{n_total}")

st.divider()

# ---- D. 정합성 배지 ----
st.subheader("정합성 배지")

RECON_LABEL = {
    "aligned": ("🟢", "정합", "가격과 유동성이 같은 시나리오를 가리킵니다."),
    "overheated": ("🔴", "과열", "가격이 유동성이 지지하는 수준을 앞서갑니다 — 연료 없이 전진."),
    "slack": ("🟡", "여유", "유동성이 가격보다 앞서 있습니다 — 상방 여력 존재."),
}

recon = scoring.reconciliation_status(position["band"] if position else None, regime)
if recon:
    icon, label, desc = RECON_LABEL[recon]
    st.markdown(f"### {icon} {label}")
    st.caption(desc)
    supported_ceiling = scoring.liquidity_supported_ceiling(levels, regime) if levels else None
    if supported_ceiling:
        st.caption(f"유동성 지지 천장: {supported_ceiling:,.0f} (regime={regime}) · 현재가 밴드: {BAND_LABEL[position['band']]}")
else:
    st.info("가격 밴드 또는 regime 중 하나가 없어 정합성을 판단할 수 없습니다.")

st.divider()

# ---- 주도 (섹터 트리맵 · RRG · key player / rising star) ----
st.subheader("주도 (섹터 · 종목)")
st.caption("연료가 지금 어느 섹터로 흐르는지 — 섹터 트리맵(크기=추적종목 시총, 색=YTD), 순환매(RRG), 주요종목.")

if market == "KOSPI":
    leadership_benchmark, _, _ = cached_kospi_level_series(365)
else:
    leadership_benchmark, _ = cached_us_price_series("nasdaq_composite", "1y")

sector_defs = sectors_config[market]["sectors"]

sector_rows = []
for code, sdef in sector_defs.items():
    if "etf" in sdef:
        sector_series, sector_err = cached_ticker_series(sdef["etf"], "ytd")
    else:
        const_series = [cached_ticker_series(tk, "ytd")[0] for tk in sdef["tickers"]]
        sector_series = scoring.build_aggregate_series(const_series)
        sector_err = None if sector_series is not None else "구성종목 조회 실패"

    market_caps = [cached_ticker_quote(tk)[1] for tk in sdef["tickers"]]
    sector_cap = sum(c for c in market_caps if c) or None

    ytd = leadership_fetcher.ytd_pct(sector_series) if sector_series is not None else None
    rs_r, rs_m = (
        scoring.compute_rs_ratio_momentum(
            sector_series, leadership_benchmark,
            ratio_window=config["rrg"]["ratio_window"], momentum_window=config["rrg"]["momentum_window"],
        )
        if sector_series is not None and leadership_benchmark is not None
        else (None, None)
    )
    sector_rows.append({
        "code": code, "name": sdef["name"], "market_cap": sector_cap,
        "ytd": ytd, "rs_ratio": rs_r, "rs_momentum": rs_m,
        "quadrant": scoring.rrg_quadrant(rs_r, rs_m), "error": sector_err,
    })

usable_rows = [r for r in sector_rows if r["market_cap"]]
if not usable_rows:
    st.info("섹터 시가총액을 하나도 못 가져왔습니다 — 일시적 조회 실패일 수 있습니다 (새로고침 시도).")
else:
    tcol1, tcol2 = st.columns([1.3, 1])
    with tcol1:
        st.caption("섹터 트리맵 — 크기: 추적종목 합산 시총 · 색: YTD%")
        fig = go.Figure(go.Treemap(
            labels=[r["name"] for r in usable_rows],
            parents=[""] * len(usable_rows),
            values=[r["market_cap"] for r in usable_rows],
            marker=dict(colors=[r["ytd"] if r["ytd"] is not None else 0 for r in usable_rows],
                        colorscale="RdYlGn", cmid=0),
            text=[f"{r['ytd']:+.0f}%" if r["ytd"] is not None else "N/A" for r in usable_rows],
            textinfo="label+text",
        ))
        fig.update_layout(height=380, margin=dict(l=4, r=4, t=4, b=4))
        st.plotly_chart(fig, width="stretch")

    with tcol2:
        st.caption("순환매 RRG — RS-Ratio(상대강도) × RS-Momentum")
        rrg_rows = [r for r in usable_rows if r["rs_ratio"] is not None]
        fig2 = go.Figure()
        if rrg_rows:
            fig2.add_hline(y=100, line_color="rgba(255,255,255,0.18)")
            fig2.add_vline(x=100, line_color="rgba(255,255,255,0.18)")
            fig2.add_trace(go.Scatter(
                x=[r["rs_ratio"] for r in rrg_rows], y=[r["rs_momentum"] for r in rrg_rows],
                mode="markers+text", text=[r["name"] for r in rrg_rows], textposition="top center",
                textfont=dict(size=9),
                marker=dict(size=13, color=[scoring.QUADRANT_COLOR.get(r["quadrant"], "gray") for r in rrg_rows],
                            line=dict(width=1, color="black")),
                showlegend=False,
            ))
        fig2.update_xaxes(title="RS-Ratio")
        fig2.update_yaxes(title="RS-Momentum")
        fig2.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig2, width="stretch")
        if len(rrg_rows) < len(usable_rows):
            st.caption(f"⚠ {len(usable_rows) - len(rrg_rows)}개 섹터는 RS 계산용 히스토리 부족으로 RRG에서 제외됨")

    st.divider()

    code_to_name = {r["code"]: r["name"] for r in sector_rows}
    default_code = max(usable_rows, key=lambda r: r["market_cap"])["code"]
    selected_code = st.selectbox(
        "섹터 선택", options=list(code_to_name.keys()), format_func=lambda c: code_to_name[c],
        index=list(code_to_name.keys()).index(default_code),
    )
    selected_def = sector_defs[selected_code]
    selected_row = next(r for r in sector_rows if r["code"] == selected_code)

    if selected_row["ytd"] is not None:
        quad_label = scoring.QUADRANT_LABEL.get(selected_row["quadrant"], "RS 데이터 부족")
        st.caption(f"{selected_row['name']} · YTD {selected_row['ytd']:+.0f}% · {quad_label}")
    else:
        st.caption(f"{selected_row['name']} · ⚠ {selected_row['error']}")

    key_tks, star_tks = selected_def.get("key", []), selected_def.get("star", [])
    if key_tks or star_tks:
        all_leader_tks = key_tks + star_tks
        leader_cols = st.columns(len(all_leader_tks))
        for col, tk in zip(leader_cols, all_leader_tks):
            price, _, _ = cached_ticker_quote(tk)
            tk_series, _ = cached_ticker_series(tk, "ytd")
            tk_ytd = leadership_fetcher.ytd_pct(tk_series)
            tag = "Key" if tk in key_tks else "Star"
            with col:
                st.markdown(f"**{tk.split('.')[0]}** `{tag}`")
                st.caption(selected_def["names"].get(tk, tk))
                st.caption(f"{price:,.1f}" if price is not None else "N/A")
                st.caption(f"YTD {tk_ytd:+.0f}%" if tk_ytd is not None else "YTD N/A")

        detail_tk = st.selectbox(
            "종목 상세", options=all_leader_tks,
            format_func=lambda t: f"{selected_def['names'].get(t, t)} ({t.split('.')[0]})",
        )
        leader = selected_def["leaders"].get(detail_tk, {})
        if leader:
            st.markdown(f"#### {selected_def['names'].get(detail_tk, detail_tk)} · {leader.get('role', '')}")
            st.write(leader.get("thesis", ""))
            if leader.get("stats"):
                stat_cols = st.columns(len(leader["stats"]))
                for sc, (k, v) in zip(stat_cols, leader["stats"]):
                    sc.metric(k, v)
            if leader.get("risk"):
                st.warning(f"리스크: {leader['risk']}")
            st.caption(f"테제 입력일: {leader.get('as_of', '-')} · 수동 큐레이션 콘텐츠 (라이브 갱신 아님)")
    else:
        names = selected_def.get("names", {})
        top_names = " · ".join(names.get(tk, tk) for tk in selected_def["tickers"])
        st.caption(f"주요종목: {top_names} (큐레이션된 key/rising star 없음)")

st.divider()

# ---- 크로스 내러티브 배지 (흐름 ▸ 여력 ▸ 주도 ▸ 정합성) — 전부 위에서 계산된 라이브 값으로 자동생성 ----
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
    recon_icon, recon_label, _ = RECON_LABEL[recon]
    recon_narrative = f"{recon_icon} {recon_label}"
else:
    recon_narrative = "⚪ 산정 불가"

with narrative_slot.container():
    st.caption("흐름 ▸ 여력 ▸ 주도 ▸ 정합성 (전부 현재 라이브 데이터에서 자동 산출 — 수동 큐레이션 없음)")
    n1, n2, n3, n4 = st.columns(4)
    n1.markdown(f"**흐름**\n\n{flow_narrative}")
    n2.markdown(f"**여력**\n\n{liquidity_narrative}")
    n3.markdown(f"**주도**\n\n{leadership_narrative}")
    n4.markdown(f"**정합성**\n\n{recon_narrative}")
    st.divider()

# ---- F. 워치리스트 ----
st.subheader("워치리스트")

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

STATUS_BADGE = {"fired": "🔴 발동", "quiet": "🟢 평시", "manual_check": "🟡 수동확인 필요", "unknown": "⚪ 데이터 없음"}
st.dataframe(
    [
        {
            "지표": r["label"],
            "트리거": r["trigger"],
            "의미": r["meaning"],
            "상태": STATUS_BADGE[r["status"]],
        }
        for r in watch_rows
    ],
    width="stretch",
    hide_index=True,
)

st.divider()


def _series_as_of(series):
    if series is None or series.empty:
        return None
    last = series.index[-1]
    return last.date() if hasattr(last, "date") else last


def oldest_thesis_as_of(sector_defs):
    dates = [
        leader.get("as_of")
        for sdef in sector_defs.values()
        for leader in sdef.get("leaders", {}).values()
        if leader.get("as_of")
    ]
    if not dates:
        return None
    return min(datetime.strptime(d, "%Y-%m-%d").date() for d in dates)


# ---- G. 히스토리: 멀티플 추이 vs 천장 밴드 ----
st.subheader("히스토리: 지수 추이 vs 천장 밴드")

if market == "KOSPI":
    hist_series, hist_source, hist_err = cached_kospi_level_series(365)
else:
    hist_series, hist_err = cached_us_price_series("nasdaq_composite", "1y")
    hist_source = "Yahoo Finance"

if levels is None:
    st.info(f"{eps_key} 값을 입력하면 천장 밴드와 함께 히스토리가 표시됩니다.")
elif hist_series is None:
    st.caption(f"⚠ 히스토리 조회 실패: {hist_err}")
else:
    fig = go.Figure()
    for scenario in scoring.BAND_ORDER:
        lo, hi = levels[scenario]
        fig.add_hrect(
            y0=lo, y1=hi, fillcolor=BAND_COLOR[scenario], line_width=0,
            annotation_text=scenario.upper(), annotation_position="top left",
        )
    fig.add_trace(go.Scatter(x=hist_series.index, y=hist_series.values, mode="lines",
                              line=dict(color="white", width=1.5), name=market))
    fig.update_yaxes(title="지수 레벨")
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")
    st.caption(f"출처: {hist_source} · 밴드는 현재 입력된 forward EPS 기준 (과거 EPS 추정치 변화는 반영되지 않음)")

st.divider()

# ---- H. 데이터 신선도 바 ----
st.subheader("데이터 신선도")

freshness_rows = [
    {"지표": f"{market} 지수레벨", "출처": source, "갱신주기": "daily", "최근갱신": as_of},
    {"지표": "Fed 대차대조표 (WALCL)", "출처": "FRED", "갱신주기": "weekly", "최근갱신": _series_as_of(walcl)},
    {"지표": "외국인 순매수 (KOSPI)", "출처": "KRX", "갱신주기": "daily", "최근갱신": _series_as_of(foreign_series)},
    {"지표": "신용잔고 (manual)", "출처": "수동입력", "갱신주기": "daily", "최근갱신": credit_as_of},
    {"지표": "KOSPI 시가총액", "출처": "KRX/수동", "갱신주기": "daily", "최근갱신": market_cap_as_of},
    {"지표": "MMF 총자산 (manual)", "출처": "수동입력", "갱신주기": "weekly", "최근갱신": mmf_as_of},
    {"지표": "USD/KRW", "출처": "FRED", "갱신주기": "daily", "최근갱신": _series_as_of(fx_series)},
    {"지표": "HY OAS", "출처": "FRED", "갱신주기": "daily", "최근갱신": _series_as_of(oas_series)},
    {"지표": "VIX", "출처": "FRED", "갱신주기": "daily", "최근갱신": _series_as_of(vix_series)},
    {"지표": "2yr 실질금리 (DFII2)", "출처": "FRED", "갱신주기": "daily", "최근갱신": real_rate_as_of},
    {"지표": f"{market} 선행EPS (manual)", "출처": "수동입력", "갱신주기": "quarterly", "최근갱신": eps_as_of},
    {"지표": "Fed 점도표 2026 인하 (manual)", "출처": "수동입력", "갱신주기": "quarterly", "최근갱신": dot_plot_as_of},
    {"지표": "시장 인상확률 (manual)", "출처": "수동입력", "갱신주기": "weekly", "최근갱신": hike_priced_as_of},
    {"지표": "외국인 보유비중 z-score (manual)", "출처": "수동입력", "갱신주기": "weekly", "최근갱신": ownership_zscore_as_of},
    {"지표": f"{market} 섹터 key/star 테제 (manual)", "출처": "수동입력(sectors.json)", "갱신주기": "quarterly",
     "최근갱신": oldest_thesis_as_of(sector_defs)},
]

STALENESS_BADGE = {"fresh": "🟢 최신", "stale": "🟡 갱신 필요", "unknown": "⚪ 미입력"}
for row in freshness_rows:
    status = manual.staleness_level(row["최근갱신"], row["갱신주기"], config)
    row["상태"] = STALENESS_BADGE[status]
    row["최근갱신"] = str(row["최근갱신"]) if row["최근갱신"] else "-"

st.dataframe(freshness_rows, width="stretch", hide_index=True)

st.caption(
    "Phase 1-7 전체 구현됨: 흐름·여력·주도·정합성 크로스 내러티브 배지 · KPI 헤더(A, Flow 레이어 포함)·"
    "천장 밴드(B)·6원천 패널(E)·regime 게이지(C)·정합성 배지(D)·섹터 트리맵/RRG/key-star 카드(주도)·"
    "워치리스트(F)·히스토리(G)·신선도 바(H). "
    "freesis/ICI 스크래핑 자동화는 보류 — manual_overrides로 대체됨."
)
