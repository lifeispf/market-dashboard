"""engine/cascade.py — Macro → Sector → Stock 타입드 캐스케이드.

정본: planning/blueprint_unified/00_architecture.md §4.3 ("통일 앱 플로우의 코드 표현").

상위 tier의 Verdict가 하위 tier의 Context(필터)가 된다:
    macro = MacroEngine.run(...)               # 루트
    sector = SectorEngine.run(.., from_macro)   # macro verdict를 context로
    stock  = StockEngine.run(.., from_sector)   # macro+sector verdict를 context로

이 한 흐름이 "Macro → Sector → Stock"을 한 줄기로 꿰는 통일 플로우의 본체다.
각 엔진은 독립 실행도 가능(/api/sectors·/api/stocks는 Context.root로 단독 호출);
본 모듈은 그 셋을 context 전파로 연결한 전체 실행이다. /api/briefing이 소비한다.

degrade 안전: 어느 tier가 비어도 다음 tier는 중립 context로 진행(절대 크래시 안 함).
"""
from __future__ import annotations

from dataclasses import dataclass

from engine.core.context import Context
from engine.core.contracts import EngineOutput
from engine.macro.engine import build_macro_engine
from engine.macro.inputs import gather_macro_inputs
from engine.macro.rulebook import MacroRulebook
from engine.sector.engine import run_sectors
from engine.stock.engine import run_stocks


@dataclass
class Cascade:
    """한 market의 전체 캐스케이드 결과."""

    market: str
    macro: EngineOutput
    sectors: list[EngineOutput]
    stocks: list[EngineOutput]

    def to_dict(self) -> dict:
        return {
            "market": self.market,
            "macro": self.macro.to_dict(),
            "sectors": [s.to_dict() for s in self.sectors],
            "stocks": [s.to_dict() for s in self.stocks],
        }


def run_cascade(market: str) -> Cascade:
    """Macro → Sector → Stock을 context 전파로 연결해 실행한다(§4.3)."""
    # 1) Macro (루트 context)
    inputs = gather_macro_inputs(market)
    macro_engine = build_macro_engine()
    macro_engine.rulebook = MacroRulebook(inputs)  # 이 실행의 raw 데이터 주입
    macro = macro_engine.run(market, Context.root(market), data=inputs)

    # 2) Sector (macro verdict를 context로 — 전 섹터 공통 상위 맥락)
    sector_ctx = Context.from_macro(macro)
    sectors = run_sectors(market, ctx=sector_ctx)

    # 3) Stock (섹터별 verdict를 context로 — §39 §5 Sector→Stock 인터페이스)
    #    각 종목은 자기 섹터의 Context를 받는다(macro+sector 체인 보존).
    ctx_by_sector = {
        s.entity_id: Context.from_sector(s, base=sector_ctx) for s in sectors
    }
    stocks = run_stocks(market, ctx_by_sector=ctx_by_sector)

    return Cascade(market=market, macro=macro, sectors=sectors, stocks=stocks)
