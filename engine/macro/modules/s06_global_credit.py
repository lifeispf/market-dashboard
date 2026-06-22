"""engine/macro/modules/s06_global_credit.py — S06 글로벌 신용·금융환경 Module.

00_architecture.md §5 매핑: `scoring.score_s06_global_credit()` (그대로 호출,
계산식 변경 없음) -> ModuleOutput. state/narrative 텍스트는
backend/api/market.py의 pre-retrofit 'Sources block'(S06 항목)을 그대로 옮긴
것이다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import ModuleOutput
from engine.macro.modules._common import headroom_state, headroom_word, to_transition

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.macro.inputs import MacroInputs


class S06GlobalCreditModule:
    """글로벌 신용·금융환경(HY OAS · VIX) 여력 관측."""

    id = "macro.S06"
    tier = "macro"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        return []

    def compute(self, entity_id: str, ctx: "Context", data: "MacroInputs") -> ModuleOutput:
        score = data.s06_score
        raw_dir = data.s06_dir

        hy_oas = data.hy_oas
        vix_value = data.vix_value
        if hy_oas is not None and vix_value is not None:
            state_text = f"HY OAS {hy_oas:.2f}% · VIX {vix_value:.1f}"
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
