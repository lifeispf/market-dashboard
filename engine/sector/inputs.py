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
from engine.core.timeframes import (
    lookback_days_for,
    normalize_tf,
    resample_for_tf,
    rrg_window_for,
    rrg_windows_for,
)

from backend.api._assembly_helpers import (
    _cached_market_cap,
    _cached_series,
    _safe,
    _ytd_slice,
)

# #1 트리맵 tf 연동: tf별 기간 수익률 계산용 거래일 수(근사).
_PERIOD_TRADING_DAYS = {"1D": 1, "1W": 5, "1M": 21, "1Q": 63, "1Y": 252}


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
    # Phase E (§21 D-12) / Phase F: 멀티-윈도우(4개) 동시관찰 RRG — ADDITIVE.
    # Phase F부터 윈도우 라벨/길이는 tf에 따라 스케일한다(rrg_windows_for(tf) —
    # 1D=1M/3M/6M/12M, 1W=3M/6M/12M/18M, ... 1Y=12M/24M/36M/60M).
    # sector_rows_to_payload()에는 포함하지 않는다(동결 7필드 payload byte-identical 보존).
    rrg_by_window: dict[str, dict[str, Any] | None] | None = None
    rrg_consensus: dict[str, Any] | None = None
    # #1 트리맵 tf 연동: 선택 tf 기간(1D/1W/1M/1Q/1Y)에 대한 섹터 수익률(%). YTD(ytd)는
    # tf 무관 고정이라 트리맵 색이 안 바뀌던 문제 해결용 — 비동결 /api/sectors envelope에만
    # 노출(동결 sectors[] payload·등가성 게이트 무관).
    period_return: float | None = None


def compute_multi_window_rrg(sector_series, benchmark_series, windows: dict[str, int]) -> tuple[dict[str, dict[str, Any] | None], dict[str, Any] | None]:
    """`windows`(라벨→거래일)로 지정된 호라이즌들의 동시관찰 RRG — §21 D-12 / Phase F.

    Phase F부터 윈도우 셋은 호출부가 넘긴다(tf-scaled — engine.core.timeframes.
    rrg_windows_for). 호환을 위해 기본 4-윈도우 동작은 호출부가 RRG_WINDOWS(또는
    rrg_windows_for("1D"))를 넘기면 그대로 재현된다.

    각 (label, W)에 대해 scoring.compute_rs_ratio_momentum(ratio_window=W,
    momentum_window=W)을 그대로 호출한다(공식 단일 출처 보존). 데이터가 모자라면
    그 윈도우는 None(절대 raise하지 않음 — scoring 자체가 None-안전).

    합의(consensus)는 None이 아닌 윈도우들의 quadrant 중 최빈값(modal)이다.
    동률이면 더 긴 윈도우 쪽을 선호한다(긴 윈도우가 더 신뢰도 높은 구조적 신호).
    하나도 해석 가능한 윈도우가 없으면 consensus=None.

    Returns:
        (rrg_by_window, consensus) — rrg_by_window는 `windows`의 모든 라벨을
        키로 갖는다(값은 dict 또는 None). consensus는
        {"quadrant", "agreement", "n"} 또는 None.
    """
    by_window: dict[str, dict[str, Any] | None] = {}
    for label, window in windows.items():
        if sector_series is None or benchmark_series is None:
            by_window[label] = None
            continue
        rs_r, rs_m = scoring.compute_rs_ratio_momentum(
            sector_series, benchmark_series, ratio_window=window, momentum_window=window,
        )
        quadrant = scoring.rrg_quadrant(rs_r, rs_m)
        by_window[label] = (
            {"ratio": rs_r, "momentum": rs_m, "quadrant": quadrant}
            if quadrant is not None
            else None
        )

    # Longer windows should win quadrant ties -> iterate from longest to shortest so
    # the first-seen max count in a tie belongs to the longest window.
    ordered_labels = sorted(windows, key=lambda lbl: windows[lbl], reverse=True)
    resolved_quadrants = [by_window[lbl]["quadrant"] for lbl in ordered_labels if by_window[lbl] is not None]
    n = len(resolved_quadrants)
    if n == 0:
        return by_window, None

    counts: dict[str, int] = {}
    first_seen_order: list[str] = []
    for q in resolved_quadrants:
        if q not in counts:
            counts[q] = 0
            first_seen_order.append(q)
        counts[q] += 1
    modal_quadrant = max(first_seen_order, key=lambda q: counts[q])
    agreement = counts[modal_quadrant] / n
    consensus = {"quadrant": modal_quadrant, "agreement": agreement, "n": n}
    return by_window, consensus


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

    lookback_days = lookback_days_for(tf)
    index_id = series_map.index_series_id(market)
    index_fetch_fn, index_source = registry[index_id]
    level_series = _cached_series(index_id, index_fetch_fn, index_source, lookback_days=lookback_days)

    benchmark_series = level_series
    sector_defs = sectors_config[market]["sectors"]
    sector_rows: list[SectorRow] = []
    benchmark_ytd = _ytd_slice(benchmark_series)
    benchmark_for_rrg = benchmark_ytd if tf == "1D" else benchmark_series

    # Phase E (§21 D-12) / Phase F: the multi-window RRG's underlying series read is
    # independent of `tf` — always read the deepest daily FULL benchmark series
    # (lookback_days_for("1Y")) regardless of the caller's tf, so that even the longest
    # tf-scaled window (e.g. 60M=1260 trading days for tf="1Y") has a chance to resolve;
    # windows.py's compute_multi_window_rrg degrades any window exceeding available history
    # to None gracefully (scoring.compute_rs_ratio_momentum's own bar-count guard). Only the
    # *window labels/lengths themselves* scale with tf via rrg_windows_for(tf) below.
    # lookback_days_for("1D") only fetches 400 calendar days, which is too shallow even for
    # the original fixed 12M(252) window, so we re-read with the deepest standard lookback.
    # _cached_series is a same-day DB read-through cache, so this is a cheap re-read (no
    # extra network fetch) when lookback_days already covers this range.
    deep_lookback_days = lookback_days_for("1Y")
    benchmark_deep_full = _cached_series(index_id, index_fetch_fn, index_source, lookback_days=deep_lookback_days)
    for code, sdef in sector_defs.items():
        if "etf" in sdef and sdef["etf"] in registry:
            etf = sdef["etf"]
            fetch_fn, source = registry[etf]
            full_series = _cached_series(etf, fetch_fn, source, lookback_days=lookback_days)
            sector_series = _ytd_slice(full_series)
            sector_series_for_rrg = sector_series if tf == "1D" else full_series
            sector_deep_full = (
                full_series if lookback_days >= deep_lookback_days
                else _cached_series(etf, fetch_fn, source, lookback_days=deep_lookback_days)
            )
        else:
            const_full = []
            for tk in sdef.get("tickers", []):
                if tk not in registry:
                    continue
                fetch_fn, source = registry[tk]
                const_full.append(_cached_series(tk, fetch_fn, source, lookback_days=lookback_days))
            const_ytd = [_ytd_slice(s) for s in const_full]
            sector_series = scoring.build_aggregate_series(const_ytd)
            sector_series_for_rrg = sector_series if tf == "1D" else scoring.build_aggregate_series(const_full)
            if lookback_days >= deep_lookback_days:
                sector_deep_full = scoring.build_aggregate_series(const_full)
            else:
                const_deep_full = []
                for tk in sdef.get("tickers", []):
                    if tk not in registry:
                        continue
                    fetch_fn, source = registry[tk]
                    const_deep_full.append(_cached_series(tk, fetch_fn, source, lookback_days=deep_lookback_days))
                sector_deep_full = scoring.build_aggregate_series(const_deep_full)

        market_caps = [_cached_market_cap(tk) for tk in sdef.get("tickers", [])]
        sector_cap = sum(c for c in market_caps if c) or None

        ytd = leadership_fetcher.ytd_pct(sector_series) if sector_series is not None else None

        resampled_sector = resample_for_tf(sector_series_for_rrg, tf)
        resampled_benchmark = resample_for_tf(benchmark_for_rrg, tf)
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

        rrg_by_window, rrg_consensus = compute_multi_window_rrg(
            sector_deep_full, benchmark_deep_full, rrg_windows_for(tf),
        )

        # #1: 선택 tf 기간 수익률(트리맵 색/라벨용). deep 일별 시리즈에서 N거래일 전 대비.
        n_back = _PERIOD_TRADING_DAYS.get(tf, 1)
        period_return = None
        if sector_deep_full is not None and len(sector_deep_full) > n_back:
            prev = sector_deep_full.iloc[-1 - n_back]
            last = sector_deep_full.iloc[-1]
            if prev:
                period_return = (last / prev - 1) * 100

        sector_rows.append(
            SectorRow(
                code=code, name=sdef["name"], market_cap=sector_cap,
                ytd=ytd, rs_ratio=rs_r, rs_momentum=rs_m, quadrant=quadrant,
                rrg_by_window=rrg_by_window, rrg_consensus=rrg_consensus,
                period_return=period_return,
            )
        )
        if tf == "1D":
            _safe(lambda code=code, sector_cap=sector_cap, ytd=ytd, rs_r=rs_r, rs_m=rs_m, quadrant=quadrant: db.upsert_sector_metric(
                market, code, today, sector_cap, ytd, rs_r, rs_m, quadrant,
            ))

    return sector_rows


def build_sector_price_series(sdef: dict, registry: dict, tf: str = "1D"):
    """섹터 하나의 가격 시리즈를 만든다(ETF-or-aggregate) — `gather_sector_inputs`의
    섹터 시리즈 구성 로직을 표준화한 ADDITIVE 헬퍼(기존 함수는 변경하지 않음).

    Phase C: `gather_stock_inputs`가 종목의 Sector-RS(자기 섹터 대비) 계산을 위해
    재사용한다. `gather_sector_inputs`와 동일한 분기(ETF 우선, 없으면 constituents
    aggregate)를 standalone으로 노출 — 호출부가 sectors_config/registry만 들고
    있으면 macro 경로 없이도 같은 섹터 시리즈를 얻을 수 있다.

    Phase D-⑥: `tf`가 tf-aware lookback(lookback_days_for)으로 시리즈를 읽고,
    tf="1D"일 때만 `_ytd_slice`를 적용한다(기존 동작과 byte-identical). 비-1D는
    backfill로 깊어진 전체 시리즈를 그대로 반환 — 이후 resample_for_tf가 처리한다.

    Returns:
        tf="1D" -> `_ytd_slice`된 섹터 가격 시리즈; 그 외 -> 전체(deep) 섹터 가격
        시리즈(pandas Series) 또는 데이터 부족 시 None.
    """
    tf = normalize_tf(tf)
    lookback_days = lookback_days_for(tf)
    if "etf" in sdef and sdef["etf"] in registry:
        etf = sdef["etf"]
        fetch_fn, source = registry[etf]
        full_series = _cached_series(etf, fetch_fn, source, lookback_days=lookback_days)
        return _ytd_slice(full_series) if tf == "1D" else full_series

    const_full = []
    for tk in sdef.get("tickers", []):
        if tk not in registry:
            continue
        fetch_fn, source = registry[tk]
        const_full.append(_cached_series(tk, fetch_fn, source, lookback_days=lookback_days))
    if tf == "1D":
        const_ytd = [_ytd_slice(s) for s in const_full]
        return scoring.build_aggregate_series(const_ytd)
    return scoring.build_aggregate_series(const_full)


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
