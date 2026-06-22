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
from config_loader import load_config, load_sectors
from data import leadership_fetcher

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


def gather_stock_inputs(market: str) -> list[StockRow]:
    """market의 모든 key/star 종목에 대해 Price-레이어 StockRow 리스트를 만든다.

    standalone — config/registry/index를 자체 구성하므로 /api/stocks가 단독
    호출 가능. DB read-through 캐시 키가 macro/leaders 경로와 동일.
    """
    config = load_config()
    sectors_config = load_sectors()
    registry = series_map.build_registry(market, sectors_config)

    index_id = series_map.index_series_id(market)
    index_fetch_fn, index_source = registry[index_id]
    level_series = _cached_series(index_id, index_fetch_fn, index_source, lookback_days=400)
    benchmark_ytd = _ytd_slice(level_series)

    ratio_window = config["rrg"]["ratio_window"]
    momentum_window = config["rrg"]["momentum_window"]

    sector_defs = sectors_config[market]["sectors"]
    rows: list[StockRow] = []
    seen: set[str] = set()
    for code, sdef in sector_defs.items():
        tickers = list(sdef.get("key", [])) + list(sdef.get("star", []))
        for tk in tickers:
            if tk in seen:
                continue
            seen.add(tk)

            full_series = None
            if tk in registry:
                fetch_fn, source = registry[tk]
                full_series = _cached_series(tk, fetch_fn, source, lookback_days=400)

            price = _last(full_series)
            if price is None:
                price, _cap, _err = _safe(lambda tk=tk: leadership_fetcher.fetch_ticker_quote(tk), (None, None, None))

            ytd_series = _ytd_slice(full_series)
            ytd = leadership_fetcher.ytd_pct(ytd_series) if ytd_series is not None else None

            rs_r, rs_m = (
                scoring.compute_rs_ratio_momentum(
                    ytd_series, benchmark_ytd,
                    ratio_window=ratio_window, momentum_window=momentum_window,
                )
                if ytd_series is not None and benchmark_ytd is not None
                else (None, None)
            )
            quadrant = scoring.rrg_quadrant(rs_r, rs_m)

            trend_dir = scoring.trend_direction(full_series, lookback=5) if full_series is not None else None
            vol = scoring.realized_volatility(full_series, window=20) if full_series is not None else None
            above_ma200 = None
            if full_series is not None and len(full_series) >= 200 and price is not None:
                ma200 = float(full_series.iloc[-200:].mean())
                above_ma200 = price >= ma200

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
                )
            )

    return rows
