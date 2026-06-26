"""engine/sector/reasoning.py — 섹터 룰베이스 추론(Why / Supports / Counter-Evidence / Invalidation).

섹터 Verdict의 narrative/supports/risks/invalidation을 §21 Relative Strength 관측
(RRG quadrant·rs_ratio/momentum·다중호라이즌 합의)에서 규칙적으로 만든다. macro와
동일 기조: 측정 조건 충족 시에만 발화, LLM 없음, 결정적·단위테스트 가능.

동결 MarketPayload의 sectors[]는 sector_rows_to_payload(7필드)에서 오고 섹터 Verdict를
쓰지 않으므로, 이 추론은 /api/sectors envelope·briefing 전용(등가성 게이트 무관).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.core.contracts import ModuleOutput

_QUAD_KR = {
    "leading": "주도",
    "improving": "순환매 진입",
    "weakening": "차익 임박",
    "lagging": "소외",
}


def build_sector_reasoning(rs: "ModuleOutput | None", macro_lead: str | None = None) -> dict[str, Any]:
    """rs: sector.relative_strength ModuleOutput(또는 None). 절대 raise 안 함."""
    if rs is None or rs.state is None:
        return {
            "narrative": "섹터 상대강도 관측 불가 — 판단 보류.",
            "supports": [],
            "risks": ["no_data"],
            "invalidation": [],
        }

    inp = rs.inputs or {}
    quadrant = inp.get("quadrant")
    rs_ratio = inp.get("rs_ratio")
    rs_mom = inp.get("rs_momentum")
    consensus = inp.get("rrg_consensus") or {}
    agreement = consensus.get("agreement")
    cons_q = consensus.get("quadrant")

    # ---- narrative(Why): 모듈 서술 + 다중호라이즌 합의 + macro 참조 ----
    parts = [rs.narrative or ""]
    if cons_q and agreement is not None:
        parts.append(f"다중호라이즌 합의 {_QUAD_KR.get(cons_q, cons_q)}({round(agreement * 100)}%)")
    if macro_lead:
        parts.append(f"macro: {macro_lead}")
    narrative = " · ".join(p for p in parts if p)

    supports: list[str] = []
    risks: list[str] = []

    # ---- quadrant 기반 찬성/반대 ----
    if quadrant == "leading":
        supports.append("RS·모멘텀 모두 시장 우위(주도 지속)")
    elif quadrant == "improving":
        supports.append("모멘텀 시장 우위 — 순환매 진입(차기 리더 후보)")
        risks.append("상대강도 아직 약함 — 확인 필요")
    elif quadrant == "weakening":
        supports.append("상대강도 우위 유지")
        risks.append("모멘텀 둔화 — 차익 임박(후반부)")
    elif quadrant == "lagging":
        risks.append("RS·모멘텀 모두 시장 열위(소외)")

    # ---- RS/모멘텀 수치(100 중심) ----
    if rs_ratio is not None:
        if rs_ratio >= 101:
            supports.append(f"상대강도 시장 우위(RS {rs_ratio:.0f})")
        elif rs_ratio <= 99:
            risks.append(f"상대강도 시장 열위(RS {rs_ratio:.0f})")
    if rs_mom is not None and rs_mom < 100 and quadrant != "weakening":
        risks.append("모멘텀 시장 열위")

    # ---- 다중호라이즌 합의 신뢰도 ----
    if agreement is not None:
        if agreement < 0.5:
            risks.append(f"다중호라이즌 합의 약함({round(agreement * 100)}%) — 신호 불안정")
        elif agreement >= 0.75 and quadrant in ("leading", "improving"):
            supports.append(f"호라이즌 일치도 높음({round(agreement * 100)}%)")

    # ---- invalidation ----
    invalidation: list[str] = []
    if quadrant in ("leading", "improving", "weakening"):
        invalidation.append("RRG quadrant 하향 전환 시 무효")
    invalidation.append("다중호라이즌 합의 붕괴(일치도 급락) 시")

    return {
        "narrative": narrative,
        "supports": supports,
        "risks": risks,
        "invalidation": invalidation,
    }
