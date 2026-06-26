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

        macro_v = upstream.upstream.get("macro") if upstream else None
        macro_lead = (macro_v.lead_pattern or macro_v.direction) if macro_v is not None else None

        # 룰베이스 추론 콘텐츠(Why/supports/risks/invalidation) — 방어적.
        try:
            from engine.sector.reasoning import build_sector_reasoning

            r = build_sector_reasoning(rs, macro_lead)
        except Exception:
            r = {"narrative": "섹터 판단 보류.", "supports": [], "risks": [], "invalidation": []}

        if rs is None or rs.state is None:
            return Verdict(
                direction="neutral", strength=0, conviction=None, lead_pattern=None,
                narrative=r["narrative"], risks=r["risks"] or ["no_data"], invalidation=r["invalidation"],
                horizon="T1", verified=False,
                extra={
                    "observed_modules": [m.module_id for m in modules],
                    "risk_profile": rs.inputs.get("risk_profile") if rs is not None else None,
                    "rrg_by_window": rs.inputs.get("rrg_by_window") if rs is not None else None,
                    "rrg_consensus": rs.inputs.get("rrg_consensus") if rs is not None else None,
                    "supports": r["supports"],
                },
            )

        if rs.state == "Leader" and rs.transition == "Weakening":
            direction, strength, pattern = _LATE_LEADER
        else:
            direction, strength, pattern = _STATE_VERDICT.get(
                rs.state, ("neutral", 2, None)
            )

        return Verdict(
            direction=direction,
            strength=strength,
            conviction=None,  # §9.1 비검증 — Breadth/Participation 추가 전까지 랭킹 신호일 뿐
            lead_pattern=pattern,
            narrative=r["narrative"],
            risks=r["risks"],
            invalidation=r["invalidation"],
            horizon="T1",
            verified=False,
            extra={
                "state": rs.state, "transition": rs.transition,
                "rs_ratio": rs.inputs.get("rs_ratio"),
                "rs_momentum": rs.inputs.get("rs_momentum"),
                "quadrant": rs.inputs.get("quadrant"),
                "approximation": rs.inputs.get("approximation"),
                "risk_profile": rs.inputs.get("risk_profile"),
                "rrg_by_window": rs.inputs.get("rrg_by_window"),
                "rrg_consensus": rs.inputs.get("rrg_consensus"),
                "supports": r["supports"],
            },
        )
