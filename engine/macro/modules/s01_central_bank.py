"""engine/macro/modules/s01_central_bank.py — S01 중앙은행 정책 Module.

00_architecture.md §5 매핑: `scoring.score_s01_central_bank()` (그대로 호출,
계산식 변경 없음) -> ModuleOutput. state/narrative 텍스트는
backend/api/market.py의 pre-retrofit 'Sources block'(S01 항목)을 그대로 옮긴
것이다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine.core.contracts import ModuleOutput
from engine.macro.modules._common import headroom_state, headroom_word, to_transition

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.macro.inputs import MacroInputs


class S01CentralBankModule:
    """중앙은행 정책(Fed WALCL · BOK) 여력 관측."""

    id = "macro.S01"
    tier = "macro"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        return []

    def compute(self, entity_id: str, ctx: "Context", data: "MacroInputs") -> ModuleOutput:
        score = data.s01_score
        raw_dir = data.s01_dir

        walcl = data.walcl
        if walcl is not None:
            state_text = f"WALCL ${float(walcl.iloc[-1]) / 1e6:.2f}T"
        else:
            state_text = "데이터 없음 (FRED_API_KEY 필요)"

        narrative = (
            f"{state_text} · {headroom_word(score)}"
            if state_text
            else headroom_word(score)
        )

        return ModuleOutput(
            module_id=self.id,
            state=headroom_state(score),
            transition=to_transition(raw_dir),
            strength=(score / 100) if score is not None else None,
            confidence=None,
            narrative=narrative,
            inputs={"raw_dir": raw_dir, "raw_score": score, "state_text": state_text},
        )
