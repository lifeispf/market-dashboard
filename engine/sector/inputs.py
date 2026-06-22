"""engine/sector/inputs.py — raw per-sector RRG metric gathering.

`gather_sector_inputs(market)` performs the exact same per-sector RRG/YTD/market-cap
computation that backend/api/market.py's `_assemble_sectors_leaders` (originally the
"Sectors / RRG / leaders" block of the `_assemble_live` monolith) does — packaged as
a list of `SectorRow`. Calculation logic is unchanged; this is a relocation so both
the new SectorEngine and the legacy sectors[] path read one definition.

RRG 원시 계산은 scoring.compute_rs_ratio_momentum / scoring.rrg_quadrant를 그대로
호출한다(§21 데이터 계약 — 같은 공식 단일 출처). 이 모듈은 fetch/원시계산만 하고
해석(State/Transition/Verdict)은 modules/·rulebook.py가 한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import scoring
from backend.store import db, series_map
from config_loader import load_config, load_sectors
from data import leadership_fetcher
from engine.core.timeframes import normalize_tf, resample_for_tf, rrg_window_for

from backend.api._assembly_helpers import (
    _cached_market_cap,
    _cached_series,
    _safe,
    _ytd_slice,
)


@dataclass
class SectorRow:
    """한 섹터의 원시 RRG metric — Module/Rulebook이 소비하는 단일 원천.

    필드는 기존 macro payload의 `sectors[]` 항목과 1:1 대응(byte-identical
    재구성 가능): code/name/market_cap/ytd/rs_ratio/rs_momentum/quadrant.
    """

    code: str
    name: str
    market_cap: float | None
    ytd: float | None
    rs_ratio: float | None
    rs_momentum: float | None
    quadrant: str | None


def gather_sector_inputs(market: str, tf: str = "1D") -> list[SectorRow]:
    """_assemble_sectors_leaders의 섹터 metric 루프를 그대로 수행해 SectorRow
    리스트를 반환한다(계산식 변경 없음 — tf="1D"는 byte-identical).

    standalone — config/sectors_config/registry/level_series를 자체 구성하므로
    /api/sectors 엔드포인트가 macro 경로 없이 단독 호출할 수 있다. DB read-through
    캐시 키가 macro 경로와 동일하므로 같은 날 동일 데이터를 본다(byte-identical).

    Phase A: `tf`는 RRG(rs_ratio/rs_momentum/quadrant)에만 영향을 준다 — 섹터/벤치마크
    시리즈를 resample_for_tf로 리샘플하고 rrg_window_for(tf)를 ratio/momentum window로
    쓴다. tf="1D"는 resample=identity·window=10(config["rrg"]와 동일)이라 기존과
    동일하다. DB upsert(sector_metrics_daily)는 tf=="1D"일 때만 수행 — 비-1D 리샘플
    값으로 일별 히스토리를 오염시키지 않는다.
    """
    tf = normalize_tf(tf)
    config = load_config()
    sectors_config = load_sectors()
    registry = series_map.build_registry(market, sectors_config)
    today = date.today()

    index_id = series_map.index_series_id(market)
    index_fetch_fn, index_source = registry[index_id]
    level_series = _cached_series(index_id, index_fetch_fn, index_source, lookback_days=400)

    benchmark_series = level_series
    sector_defs = sectors_config[market]["sectors"]
    sector_rows: list[SectorRow] = []
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
            const_ytd = [_ytd_slice(s) for s in const_full]
            sector_series = scoring.build_aggregate_series(const_ytd)

        market_caps = [_cached_market_cap(tk) for tk in sdef.get("tickers", [])]
        sector_cap = sum(c for c in market_caps if c) or None

        ytd = leadership_fetcher.ytd_pct(sector_series) if sector_series is not None else None

        resampled_sector = resample_for_tf(sector_series, tf)
        resampled_benchmark = resample_for_tf(benchmark_ytd, tf)
        rrg_window = rrg_window_for(tf)
        rs_r, rs_m = (
            scoring.compute_rs_ratio_momentum(
                resampled_sector, resampled_benchmark,
                ratio_window=rrg_window, momentum_window=rrg_window,
            )
            if resampled_sector is not None and resampled_benchmark is not None
            else (None, None)
        )
        quadrant = scoring.rrg_quadrant(rs_r, rs_m)
        sector_rows.append(
            SectorRow(
                code=code, name=sdef["name"], market_cap=sector_cap,
                ytd=ytd, rs_ratio=rs_r, rs_momentum=rs_m, quadrant=quadrant,
            )
        )
        if tf == "1D":
            _safe(lambda code=code, sector_cap=sector_cap, ytd=ytd, rs_r=rs_r, rs_m=rs_m, quadrant=quadrant: db.upsert_sector_metric(
                market, code, today, sector_cap, ytd, rs_r, rs_m, quadrant,
            ))

    return sector_rows


def build_sector_price_series(sdef: dict, registry: dict):
    """섹터 하나의 YTD 가격 시리즈를 만든다(ETF-or-aggregate) — `gather_sector_inputs`의
    섹터 시리즈 구성 로직을 표준화한 ADDITIVE 헬퍼(기존 함수는 변경하지 않음).

    Phase C: `gather_stock_inputs`가 종목의 Sector-RS(자기 섹터 대비) 계산을 위해
    재사용한다. `gather_sector_inputs`와 동일한 분기(ETF 우선, 없으면 constituents
    aggregate)를 standalone으로 노출 — 호출부가 sectors_config/registry만 들고
    있으면 macro 경로 없이도 같은 섹터 시리즈를 얻을 수 있다.

    Returns:
        `_ytd_slice`된 섹터 가격 시리즈(pandas Series) 또는 데이터 부족 시 None.
    """
    if "etf" in sdef and sdef["etf"] in registry:
        etf = sdef["etf"]
        fetch_fn, source = registry[etf]
        full_series = _cached_series(etf, fetch_fn, source, lookback_days=400)
        return _ytd_slice(full_series)

    const_full = []
    for tk in sdef.get("tickers", []):
        if tk not in registry:
            continue
        fetch_fn, source = registry[tk]
        const_full.append(_cached_series(tk, fetch_fn, source, lookback_days=400))
    const_ytd = [_ytd_slice(s) for s in const_full]
    return scoring.build_aggregate_series(const_ytd)


def sector_rows_to_payload(rows: list[SectorRow]) -> list[dict[str, Any]]:
    """SectorRow 리스트를 동결 `sectors[]` payload shape(camelCase)로 매핑한다.

    backend/api/market.py:_assemble_sectors_leaders가 이 함수로 기존과
    byte-identical한 sectors_out을 만든다.
    """
    return [
        {
            "code": r.code, "name": r.name, "marketCap": r.market_cap, "ytd": r.ytd,
            "rsRatio": r.rs_ratio, "rsMomentum": r.rs_momentum, "quadrant": r.quadrant,
        }
        for r in rows
    ]
