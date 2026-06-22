"""engine/macro/modules/fear_greed.py — §13-1 Fear & Greed Module.

00_architecture.md §5 매핑: `scoring_ext.fear_greed()` 결과(이미
engine/macro/inputs.py:gather_macro_inputs()가 그대로 호출해 계산해 둔
data.fear_greed)를 ModuleOutput으로 감싼다. 계산식 변경 없음 -- 이 모듈은
기존 fear_greed dict를 재해석하지 않고 그대로 보존한다.

REGIME(S01-S06)과 완전히 독립적인 별도 심리/포지셔닝 축이라는 scoring_ext.py
docstring의 원칙을 그대로 유지 -- 절대 S01-S06과 합산하지 않는다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import ModuleOutput

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.macro.inputs import MacroInputs


class FearGreedModule:
    """시장 심리/포지셔닝(§13-1 F1-F4 MVP) 관측 -- REGIME과 별개 축."""

    id = "macro.fear_greed"
    tier = "macro"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        return []

    def compute(self, entity_id: str, ctx: "Context", data: "MacroInputs") -> ModuleOutput:
        fg = data.fear_greed
        score = fg.get("score") if fg else None
        label = fg.get("label") if fg else None

        return ModuleOutput(
            module_id=self.id,
            state=label,
            transition=None,  # fear_greed has no trend-direction concept in scoring_ext.py
            strength=(score / 100) if score is not None else None,
            confidence=None,
            narrative=f"공포탐욕 {label} (nAvailable={fg.get('nAvailable')}/{fg.get('nTotal')})" if fg else "공포탐욕 산정 불가",
            # The adapter reads payload["fearGreed"] straight off this -- the entire
            # original dict is preserved untouched so it flows through byte-identical.
            inputs={"fear_greed": fg},
        )
