"""engine/sector/rulebook.py — SectorRulebook.

정본: blueprint_micro/sector_engine/29_rulebook.md (패턴 A~J, Veto V1~V4).

ModuleOutput들을 해석해 섹터 Verdict를 산출한다 — fetch/합산 없이 패턴 매칭만.
현 단계는 §21 Relative Strength 한 축만 가용하므로(나머지 모듈은 데이터 평면
이후), 29_rulebook.md의 10개 패턴 중 RS 단독으로 식별 가능한 부분집합만
적용한다. Breadth/Participation/Catalyst가 들어오면 충돌 패턴(Mega-cap
Dependence, False Leadership 등)을 추가한다.

상위(macro) Verdict는 upstream Context로 들어온다(§4.3 캐스케이드). 현재는
narrative에 macro regime을 참조로 노출하고, 강한 macro down일 때 conviction을
낮추는 §39 §5식 보정 자리를 마련해 둔다(실제 보정은 conviction이 검증된 뒤).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import Verdict

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.core.contracts import ModuleOutput

# §21 State -> (Direction, Verdict.strength 0..4, §29 lead_pattern 부분집합).
_STATE_VERDICT = {
    "Leader": ("strong_up", 4, "Strong Leader"),
    "Emerging": ("up", 3, "Early Rotation"),
    "Lagging": ("down", 1, "Breakdown"),
}
# State="Leader" + transition="Weakening"는 후반부 — 별도 패턴으로 강등.
_LATE_LEADER = ("neutral", 2, "Late Leader")


class SectorRulebook:
    """섹터 해석기 — §21 중심으로 Verdict 산출(합산 없음, 패턴 매칭만)."""

    def interpret(self, modules: "list[ModuleOutput]", upstream: "Context") -> Verdict:
        rs = next((m for m in modules if m.module_id == "sector.relative_strength"), None)

        if rs is None or rs.state is None:
            return Verdict(
                direction="neutral", strength=0, conviction=None, lead_pattern=None,
                narrative="섹터 상대강도 관측 불가 — 판단 보류.",
                risks=["no_data"], invalidation=[], horizon="T1", verified=False,
                extra={
                    "observed_modules": [m.module_id for m in modules],
                    "risk_profile": rs.inputs.get("risk_profile") if rs is not None else None,
                },
            )

        if rs.state == "Leader" and rs.transition == "Weakening":
            direction, strength, pattern = _LATE_LEADER
        else:
            direction, strength, pattern = _STATE_VERDICT.get(
                rs.state, ("neutral", 2, None)
            )

        macro_v = upstream.upstream.get("macro") if upstream else None
        macro_note = ""
        if macro_v is not None:
            macro_note = f" (macro regime: {macro_v.lead_pattern or macro_v.direction})"

        risks: list[str] = []
        if rs.transition == "Weakening":
            risks.append("모멘텀 둔화 — 차익 임박")
        if rs.state == "Emerging":
            risks.append("상대강도 미확인 — Breadth/Participation 검증 필요")

        return Verdict(
            direction=direction,
            strength=strength,
            conviction=None,  # §9.1 비검증 — Breadth/Participation 추가 전까지 랭킹 신호일 뿐
            lead_pattern=pattern,
            narrative=(rs.narrative or "") + macro_note,
            risks=risks,
            invalidation=[],
            horizon="T1",
            verified=False,
            extra={
                "state": rs.state, "transition": rs.transition,
                "rs_ratio": rs.inputs.get("rs_ratio"),
                "rs_momentum": rs.inputs.get("rs_momentum"),
                "quadrant": rs.inputs.get("quadrant"),
                "approximation": rs.inputs.get("approximation"),
                "risk_profile": rs.inputs.get("risk_profile"),
            },
        )
