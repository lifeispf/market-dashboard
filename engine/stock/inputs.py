"""engine/stock/inputs.py — raw per-stock price-layer metric gathering.

`gather_stock_inputs(market)`는 sectors.json의 모든 key/star 종목(레거시 `leaders`
대상)을 돌며 종목별 가격 시리즈에서 Price 레이어 원시 지표를 계산한다:
  - Market RS: scoring.compute_rs_ratio_momentum(종목 YTD, 지수 YTD) → quadrant
    (sector §21과 동일 공식 — §35 데이터 계약).
  - Price Structure: scoring.trend_direction / realized_volatility / 200MA 위치.

계산식은 scoring.py를 그대로 호출(새 계산 없음). fetch/원시계산만 하고 해석
(State/Verdict)은 modules/·rulebook.py가 한다. close-only 시리즈라 §36
Participation(거래량)·§32/§33(펀더멘털·기대·포지셔닝)은 여기서 다루지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import scoring
from backend.store import series_map
from config_loader import load_sectors
from data import leadership_fetcher
from engine.core.timeframes import lookback_days_for, normalize_tf, resample_for_tf, rrg_window_for
from engine.sector.inputs import build_sector_price_series

from backend.api._assembly_helpers import (
    _cached_series,
    _last,
    _safe,
    _ytd_slice,
)


@dataclass
class StockRow:
    """한 종목의 원시 Price-레이어 지표 — Module/Rulebook이 소비하는 단일 원천."""

    ticker: str
    name: str
    sector_code: str
    sector_name: str
    price: float | None
    ytd: float | None
    # §35 Market RS (vs index)
    rs_ratio: float | None
    rs_momentum: float | None
    quadrant: str | None
    # §34 Price Structure
    trend_dir: str | None       # "up" | "down" | "flat" | None
    vol: float | None           # realized volatility (20d)
    above_ma200: bool | None    # price >= 200d MA (None = 데이터 부족)
    # Phase C: Sector RS (vs 자기 섹터 시리즈) — Market RS와 동일 공식, 벤치마크만 교체.
    sector_rs_ratio: float | None = None
    sector_rs_momentum: float | None = None
    sector_quadrant: str | None = None
    # DI-3 Action: 투명 룰 손절 레벨용(MA200 값·최근 20일 저점). 동결 payload 무관(envelope 전용).
    ma200: float | None = None
    low_20: float | None = None


def gather_stock_inputs(market: str, tf: str = "1D") -> list[StockRow]:
    """market의 모든 key/star 종목에 대해 Price-레이어 StockRow 리스트를 만든다.

    standalone — config/registry/index를 자체 구성하므로 /api/stocks가 단독
    호출 가능. DB read-through 캐시 키가 macro/leaders 경로와 동일.

    Phase A: `tf`는 Market RS(rs_ratio/rs_momentum/quadrant, vs 지수)에만 영향을
    준다 — 종목 YTD/벤치마크 시리즈를 resample_for_tf로 리샘플하고 rrg_window_for(tf)
    를 ratio/momentum window로 쓴다. tf="1D"는 identity·window=10이라 기존과 동일.
    Price-구조 필드(trend_dir/vol/above_ma200)는 Phase A에서 현행 일별 계산 그대로
    유지한다.

    Phase C: Sector-RS(sector_rs_ratio/sector_rs_momentum/sector_quadrant, vs 자기
    섹터 시리즈)를 추가로 계산한다. 섹터 시리즈는 `engine.sector.inputs.
    build_sector_price_series`(ETF-or-aggregate, gather_sector_inputs와 동일 로직)로
    구성하고, Market RS와 동일하게 resample_for_tf + rrg_window_for(tf)를 적용한다.
    sector_defs를 순회하므로 섹터 시리즈는 섹터당 한 번만 계산(캐시 재사용).
    """
    tf = normalize_tf(tf)
    sectors_config = load_sectors()
    registry = series_map.build_registry(market, sectors_config)
    lookback_days = lookback_days_for(tf)

    index_id = series_map.index_series_id(market)
    index_fetch_fn, index_source = registry[index_id]
    level_series = _cached_series(index_id, index_fetch_fn, index_source, lookback_days=lookback_days)
    benchmark_ytd = _ytd_slice(level_series)
    benchmark_rrg = benchmark_ytd if tf == "1D" else level_series
    resampled_benchmark = resample_for_tf(benchmark_rrg, tf)
    rrg_window = rrg_window_for(tf)

    sector_defs = sectors_config[market]["sectors"]
    rows: list[StockRow] = []
    seen: set[str] = set()
    for code, sdef in sector_defs.items():
        # Phase C: 이 섹터의 가격 시리즈(ETF-or-aggregate) — 섹터당 한 번만 구성해
        # 그 섹터의 모든 종목이 재사용한다(gather_sector_inputs와 동일 로직, 읽기전용
        # 헬퍼로 replicate — gather_sector_inputs 자체는 무수정).
        sector_ytd_series = build_sector_price_series(sdef, registry, tf)
        resampled_sector_series = resample_for_tf(sector_ytd_series, tf)

        tickers = list(sdef.get("key", [])) + list(sdef.get("star", []))
        for tk in tickers:
            if tk in seen:
                continue
            seen.add(tk)

            full_series = None
            if tk in registry:
                fetch_fn, source = registry[tk]
                full_series = _cached_series(tk, fetch_fn, source, lookback_days=lookback_days)

            price = _last(full_series)
            if price is None:
                price, _cap, _err = _safe(lambda tk=tk: leadership_fetcher.fetch_ticker_quote(tk), (None, None, None))

            ytd_series = _ytd_slice(full_series)
            ytd = leadership_fetcher.ytd_pct(ytd_series) if ytd_series is not None else None

            stock_rrg_input = ytd_series if tf == "1D" else full_series
            resampled_ytd = resample_for_tf(stock_rrg_input, tf)
            rs_r, rs_m = (
                scoring.compute_rs_ratio_momentum(
                    resampled_ytd, resampled_benchmark,
                    ratio_window=rrg_window, momentum_window=rrg_window,
                )
                if resampled_ytd is not None and resampled_benchmark is not None
                else (None, None)
            )
            quadrant = scoring.rrg_quadrant(rs_r, rs_m)

            # Phase C: Sector RS — Market RS와 동일 공식, 벤치마크만 자기 섹터 시리즈로 교체.
            sector_rs_r, sector_rs_m = (
                scoring.compute_rs_ratio_momentum(
                    resampled_ytd, resampled_sector_series,
                    ratio_window=rrg_window, momentum_window=rrg_window,
                )
                if resampled_ytd is not None and resampled_sector_series is not None
                else (None, None)
            )
            sector_quadrant = scoring.rrg_quadrant(sector_rs_r, sector_rs_m)

            trend_dir = scoring.trend_direction(full_series, lookback=5) if full_series is not None else None
            vol = scoring.realized_volatility(full_series, window=20) if full_series is not None else None
            above_ma200 = None
            ma200 = None
            low_20 = None
            if full_series is not None and len(full_series) >= 200 and price is not None:
                ma200 = float(full_series.iloc[-200:].mean())
                above_ma200 = price >= ma200
            if full_series is not None and len(full_series) >= 20:
                low_20 = float(full_series.iloc[-20:].min())

            rows.append(
                StockRow(
                    ticker=tk,
                    name=sdef.get("names", {}).get(tk, tk),
                    sector_code=code,
                    sector_name=sdef["name"],
                    price=price,
                    ytd=ytd,
                    rs_ratio=rs_r,
                    rs_momentum=rs_m,
                    quadrant=quadrant,
                    trend_dir=trend_dir,
                    vol=vol,
                    above_ma200=above_ma200,
                    sector_rs_ratio=sector_rs_r,
                    sector_rs_momentum=sector_rs_m,
                    sector_quadrant=sector_quadrant,
                    ma200=ma200,
                    low_20=low_20,
                )
            )

    return rows
