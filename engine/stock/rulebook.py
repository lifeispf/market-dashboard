"""engine/stock/rulebook.py — StockRulebook.

정본: blueprint_micro/stock_engine/39_rulebook.md (패턴 A~J, 거부권 축, Sector→
Stock 인터페이스 §5, position_size_hint).

ModuleOutput들을 해석해 종목 Verdict를 산출 — fetch/합산 없이 패턴 매칭 + 거부권만.
현 단계는 Price 레이어 2축(§35 RS, §34 Price Structure)만 가용하므로 §39의 10개
패턴 중 이 둘로 식별 가능한 부분집합만 적용한다. Quality/Expectation/Positioning이
들어오면 Value Trap·Crowded Momentum·Story Without Numbers 등을 추가한다.

거부권(§34/§35): Price Structure = Broken -> Long 금지(direction 강등, size=avoid).
Sector→Stock 인터페이스(§39 §5): 상위 Sector Verdict가 강한 하락/Breakdown이면
종목 direction을 한 단계 강등(캐스케이드 필터). conviction은 비검증이라 None 유지.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import Verdict

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.core.contracts import ModuleOutput

# direction 한 단계 강등(캐스케이드/거부권용).
_DOWNGRADE = {"strong_up": "up", "up": "neutral", "neutral": "down", "down": "strong_down", "strong_down": "strong_down"}


def _pattern(rs_state: str | None, struct_state: str | None) -> tuple[str, str, int, str]:
    """(rs_state, struct_state) -> (direction, lead_pattern, strength 0..4, size_hint).

    §34 Broken은 호출 전에 veto로 처리하므로 여기 도달하지 않는다.
    """
    # §39 archetype 부분집합 (Price 레이어 2축 기준)
    if rs_state in ("Leader", "Dominant Leader") and struct_state == "Constructive":
        return "strong_up", "Trend Leader", 4, "full"
    if rs_state == "Emerging" and struct_state in ("Constructive", "Neutral"):
        return "up", "Early Stage Breakout", 3, "half"
    if rs_state in ("Leader", "Average") and struct_state == "Extended":
        # 추세는 강하나 위치 나쁨 — 신규 진입 비추천(§34 Extended Winner)
        return "neutral", "Extended Winner", 2, "quarter"
    if rs_state == "Lagging":
        return "down", "Lagging", 1, "avoid"
    if rs_state in ("Leader", "Dominant Leader") and struct_state == "Neutral":
        return "up", "Trend Leader", 3, "half"
    return "neutral", "Mixed", 2, "quarter"


class StockRulebook:
    """개별주 해석기 — §35×§34 패턴 매칭 + Broken veto + Sector 캐스케이드."""

    def interpret(self, modules: "list[ModuleOutput]", upstream: "Context") -> Verdict:
        rs = next((m for m in modules if m.module_id == "stock.relative_strength"), None)
        ps = next((m for m in modules if m.module_id == "stock.price_structure"), None)
        rs_state = rs.state if rs else None
        struct_state = ps.state if ps else None

        if rs_state is None and struct_state is None:
            return Verdict(
                direction="neutral", strength=0, conviction=None, lead_pattern=None,
                narrative="종목 가격 관측 불가 — 판단 보류.", risks=["no_data"], invalidation=[],
                horizon="T1", verified=False, extra={"position_size_hint": "avoid"},
            )

        risks: list[str] = []
        vetoed = False
        if struct_state == "Broken":
            # §34 거부권: 구조 붕괴 -> Long 금지
            direction, lead_pattern, strength, size = "down", "Stage 4 Decline", 1, "avoid"
            risks.append("가격 구조 붕괴(200MA 아래·하락 추세) — 신규 매수 금지")
            vetoed = True
        else:
            direction, lead_pattern, strength, size = _pattern(rs_state, struct_state)

        if rs_state == "Lagging" and not vetoed:
            risks.append("상대강도 열위 — 시장 미인정")
        if struct_state == "Extended":
            risks.append("추세 둔화 — 신규 진입 위치 불리")

        # Sector→Stock 캐스케이드(§39 §5): 상위 섹터가 강한 하락/Breakdown이면 강등.
        sector_v = upstream.upstream.get("sector") if upstream else None
        cascade_note = ""
        if sector_v is not None:
            if sector_v.direction == "strong_down" or sector_v.lead_pattern == "Breakdown":
                direction = _DOWNGRADE[direction]
                if size == "full":
                    size = "half"
                elif size == "half":
                    size = "quarter"
                risks.append("소속 섹터 약세 — 포지션 축소(캐스케이드 강등)")
                cascade_note = " · 섹터 약세로 강등"
            elif sector_v.direction == "strong_up":
                cascade_note = " · 섹터 강세 배경"

        narr_bits = [b for b in [rs.narrative if rs else None, ps.narrative if ps else None] if b]
        narrative = " / ".join(narr_bits) + cascade_note

        return Verdict(
            direction=direction, strength=strength,
            conviction=None,  # §9.1 비검증 — Quality/Expectation 추가 전까지 랭킹 신호일 뿐
            lead_pattern=lead_pattern, narrative=narrative, risks=risks, invalidation=[],
            horizon="T1", verified=False,
            extra={
                "position_size_hint": size,
                "rs_state": rs_state, "struct_state": struct_state,
                "quadrant": rs.inputs.get("quadrant") if rs else None,
                "trend_dir": ps.inputs.get("trend_dir") if ps else None,
                "above_ma200": ps.inputs.get("above_ma200") if ps else None,
            },
        )
