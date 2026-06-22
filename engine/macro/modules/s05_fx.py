"""engine/macro/modules/s05_fx.py — S05 원/달러 환율 Module.

00_architecture.md §5 매핑: `scoring.score_s05_fx()` (그대로 호출, 계산식
변경 없음) -> ModuleOutput. state/narrative 텍스트는 backend/api/market.py의
pre-retrofit 'Sources block'(S05 항목)을 그대로 옮긴 것이다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import ModuleOutput
from engine.macro.modules._common import headroom_state, headroom_word, to_transition

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.macro.inputs import MacroInputs


class S05FxModule:
    """원/달러 환율(증폭기/게이트) 여력 관측."""

    id = "macro.S05"
    tier = "macro"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        return []

    def compute(self, entity_id: str, ctx: "Context", data: "MacroInputs") -> ModuleOutput:
        score = data.s05_score
        raw_dir = data.s05_dir

        usdkrw = data.usdkrw
        if usdkrw is not None:
            state_text = f"USD/KRW {usdkrw:,.1f}"
        else:
            state_text = "데이터 없음 (FRED_API_KEY 필요)"

        narrative = f"{state_text} · {headroom_word(score)}"

        return ModuleOutput(
            module_id=self.id,
            state=headroom_state(score),
            transition=to_transition(raw_dir),
            strength=(score / 100) if score is not None else None,
            confidence=None,
            narrative=narrative,
            inputs={"raw_dir": raw_dir, "raw_score": score, "state_text": state_text},
        )
