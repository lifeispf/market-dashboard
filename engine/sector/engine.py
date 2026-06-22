"""engine/sector/engine.py — Sector tier Engine 조립 + 실행 헬퍼.

정본: planning/blueprint_unified/00_architecture.md §4.2/§4.3.

build_sector_engine()는 core.Engine(tier="sector")에 §21 모듈을 싣고
SectorRulebook을 붙인다. run_sectors()는 한 market의 모든 섹터를 돌며
섹터별 EngineOutput 리스트를 만든다 — 각 섹터가 entity_id가 된다.

Module.compute(entity_id, ctx, data)의 data 인자로는 해당 섹터의 SectorRow를
넘긴다(섹터마다 다른 raw 입력). Engine.run의 data 인자가 곧 그 SectorRow다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.context import Context
from engine.core.engine import Engine
from engine.sector.inputs import gather_sector_inputs
from engine.sector.modules.relative_strength import SectorRelativeStrengthModule
from engine.sector.rulebook import SectorRulebook

if TYPE_CHECKING:
    from engine.core.contracts import EngineOutput


def build_sector_engine() -> Engine:
    """sector tier Engine을 조립한다 — 현재 §21 Relative Strength 1모듈."""
    return Engine(
        tier="sector",
        modules=[SectorRelativeStrengthModule()],
        rulebook=SectorRulebook(),
    )


def run_sectors(market: str, ctx: "Context | None" = None, tf: str = "1D") -> list["EngineOutput"]:
    """market의 모든 섹터를 Sector Engine으로 돌려 EngineOutput 리스트 반환.

    Args:
        market: "KOSPI" | "NASDAQ".
        ctx: 상위(macro) Context. None이면 Context.root(market)로 단독 실행
            (캐스케이드 없이) — /api/sectors 단독 호출용. 전체 캐스케이드
            (macro→sector)는 /api/briefing이 Context.from_macro로 주입한다.
        tf: 타임프레임("1D"|"1W"|"1M"|"1Q"|"1Y", 기본 "1D") — RRG 리샘플/윈도우
            번들을 결정한다(engine/core/timeframes.py). 기본값은 기존과 동일.

    Returns:
        섹터별 EngineOutput 리스트(entity_id = 섹터 code).
    """
    if ctx is None:
        ctx = Context.root(market)
    engine = build_sector_engine()
    rows = gather_sector_inputs(market, tf=tf)
    return [engine.run(row.code, ctx, data=row) for row in rows]
