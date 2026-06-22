"""engine/macro/modules/s04_dry_powder.py — S04 美 대기자금·자사주 Module.

00_architecture.md §5 매핑: `scoring.score_s04_dry_powder()` (그대로 호출,
계산식 변경 없음) -> ModuleOutput. state/narrative 텍스트는
backend/api/market.py의 pre-retrofit 'Sources block'(S04 항목)을 그대로 옮긴
것이다.

주의: 원본 dir_map에서 S04는 항상 None이었다(MMF 총자산은 추세 방향을 계산하지
않음) -- 이 모듈도 raw_dir을 항상 None으로 보존해 동일하게 동작한다.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import ModuleOutput
from engine.macro.modules._common import headroom_state, headroom_word, to_transition

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.macro.inputs import MacroInputs


class S04DryPowderModule:
    """美 대기자금(MMF)·자사주 여력 관측."""

    id = "macro.S04"
    tier = "macro"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        return []

    def compute(self, entity_id: str, ctx: "Context", data: "MacroInputs") -> ModuleOutput:
        score = data.s04_score
        raw_dir = None  # market.py pre-retrofit dir_map["S04"] was always None

        mmf_value = data.mmf_value
        if mmf_value:
            state_text = f"MMF ${mmf_value / 1e12:,.2f}T"
        else:
            state_text = "미입력 (manual_overrides.mmf_total_usd)"

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
