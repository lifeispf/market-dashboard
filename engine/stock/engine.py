"""engine/stock/engine.py — Stock tier Engine 조립 + 실행 헬퍼.

정본: 00_architecture.md §4.2/§4.3, blueprint_micro/stock_engine/.

build_stock_engine()는 core.Engine(tier="stock")에 Price 레이어 2모듈(§35 RS, §34
Price Structure)을 싣고 StockRulebook을 붙인다. run_stocks()는 한 market의 모든
key/star 종목을 돌며 종목별 EngineOutput을 만든다 — 각 종목이 entity_id(ticker).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.context import Context
from engine.core.engine import Engine
from engine.stock.inputs import gather_stock_inputs
from engine.stock.modules.price_structure import StockPriceStructureModule
from engine.stock.modules.relative_strength import StockRelativeStrengthModule
from engine.stock.rulebook import StockRulebook

if TYPE_CHECKING:
    from engine.core.contracts import EngineOutput
    from engine.stock.inputs import StockRow


def build_stock_engine() -> Engine:
    """stock tier Engine을 조립한다 — Price 레이어 §35 RS + §34 Price Structure."""
    return Engine(
        tier="stock",
        modules=[StockRelativeStrengthModule(), StockPriceStructureModule()],
        rulebook=StockRulebook(),
    )


def run_stocks(
    market: str,
    ctx_by_sector: "dict[str, Context] | None" = None,
    tf: str = "1D",
) -> list["EngineOutput"]:
    """market의 모든 key/star 종목을 Stock Engine으로 돌려 EngineOutput 리스트 반환.

    Args:
        market: "KOSPI" | "NASDAQ".
        ctx_by_sector: 섹터코드 -> 그 섹터의 Context(상위 sector verdict 포함).
            None이면 종목마다 Context.root(market)로 단독 실행(캐스케이드 없음).
            전체 캐스케이드(macro→sector→stock)는 /api/briefing이 주입한다.
        tf: 타임프레임("1D"|"1W"|"1M"|"1Q"|"1Y", 기본 "1D") — Market RS 리샘플/
            윈도우 번들을 결정한다. 기본값은 기존과 동일.

    Returns:
        종목별 EngineOutput 리스트(entity_id = ticker).
    """
    engine = build_stock_engine()
    rows: list[StockRow] = gather_stock_inputs(market, tf=tf)
    outputs: list[EngineOutput] = []
    for row in rows:
        if ctx_by_sector and row.sector_code in ctx_by_sector:
            ctx = ctx_by_sector[row.sector_code]
        else:
            ctx = Context.root(market)
        outputs.append(engine.run(row.ticker, ctx, data=row))
    return outputs
