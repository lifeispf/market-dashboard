"""engine/macro/engine.py — build_macro_engine().

00_architecture.md §5/§10: macro tier = S01~S06 + fear_greed 모듈 6+1개 +
MacroRulebook 1개를 core.Engine으로 묶는다. entity_id는 호출자가
engine.run(market, ctx, data=inputs)로 넘기는 market 문자열이다.

사용 패턴 (backend/api/market.py의 새 _assemble_live가 따르는 방식):
    inputs = gather_macro_inputs(market)
    engine = build_macro_engine()
    engine.rulebook = MacroRulebook(inputs)   # 이 실행의 MacroInputs를 주입
    engine_output = engine.run(market, Context.root(market), data=inputs)

rulebook을 build_macro_engine() 호출 시점이 아니라 run() 직전에 주입하는 것은
MacroRulebook이 매 요청(market별 raw 계산 결과)마다 달라지는 MacroInputs를
필요로 하기 때문이다(rulebook.py 모듈 docstring 참조) -- build_macro_engine()
은 무상태 모듈 목록만 조립하는 순수 팩토리로 남는다.
"""
from __future__ import annotations

from engine.core.engine import Engine
from engine.macro.modules.fear_greed import FearGreedModule
from engine.macro.modules.s01_central_bank import S01CentralBankModule
from engine.macro.modules.s02_foreign_flow import S02ForeignFlowModule
from engine.macro.modules.s03_domestic_credit import S03DomesticCreditModule
from engine.macro.modules.s04_dry_powder import S04DryPowderModule
from engine.macro.modules.s05_fx import S05FxModule
from engine.macro.modules.s06_global_credit import S06GlobalCreditModule
from engine.macro.rulebook import MacroRulebook


def build_macro_engine() -> Engine:
    """macro tier Engine을 조립한다 -- S01~S06 + fear_greed 6+1 모듈.

    rulebook은 inputs=None인 MacroRulebook()으로 초기화된다(이 시점에는 아직
    어떤 market의 MacroInputs도 없다). 호출자가 engine.run() 직전에
    `engine.rulebook = MacroRulebook(inputs)`로 이 실행의 MacroInputs를
    주입해야 한다.
    """
    return Engine(
        tier="macro",
        modules=[
            S01CentralBankModule(),
            S02ForeignFlowModule(),
            S03DomesticCreditModule(),
            S04DryPowderModule(),
            S05FxModule(),
            S06GlobalCreditModule(),
            FearGreedModule(),
        ],
        rulebook=MacroRulebook(),
    )
