"""engine/stock/modules/relative_strength.py — §35 Relative Strength (Market RS).

정본: blueprint_micro/stock_engine/35_relative_strength.md ("주가는 시장의 투표
결과이며 RS는 그 결과를 측정한다").

청사진 §35는 3계층 RS(Market/Sector/Peer)를 요구하지만, 데이터 계약(§35-6)상
Sector RS는 Sector §21 출력 재사용, Peer RS는 동종기업 비교 데이터 필요. 본 단계는
**Market RS(종목 vs 지수)만** 구현 — scoring RRG 단일 윈도우(§21·sector와 동일
공식). Sector RS 재사용·Peer RS는 캐스케이드/데이터 평면 이후 보강.

State 어휘(§35): Dominant Leader/Leader/Emerging/Average/Lagging. 단일 윈도우
근사이므로 quadrant 기반 coarse 매핑이며 strength/confidence는 비검증 휴리스틱(§9.1).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import ModuleOutput

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.stock.inputs import StockRow

# RRG quadrant -> (State, Transition, coarse strength 0..1). sector §21과 같은
# 해석이되 State 어휘는 §35(Leader/Emerging/Average/Lagging)를 따른다.
_QUADRANT_INTERPRETATION = {
    "leading": ("Leader", "Stable", 0.9),
    "improving": ("Emerging", "Improving", 0.65),
    "weakening": ("Average", "Weakening", 0.45),
    "lagging": ("Lagging", "Stable", 0.2),
}

_QUADRANT_NARRATIVE = {
    "leading": "시장 대비 상대강도·모멘텀 모두 우위 — 리더십 유지.",
    "improving": "상대강도는 아직 평균 이하지만 모멘텀이 시장을 앞선다 — 부상 중(차기 리더 후보).",
    "weakening": "상대강도는 평균 이상이나 모멘텀 둔화 — 리더십 약화 조짐.",
    "lagging": "시장 대비 상대강도·모멘텀 모두 열위 — 소외.",
}


class StockRelativeStrengthModule:
    """§35 — 종목의 시장(지수) 대비 상대강도 관측(Market RS, RRG 단일 윈도우 근사)."""

    id = "stock.relative_strength"
    tier = "stock"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        return []

    def compute(self, entity_id: str, ctx: "Context", data: "StockRow") -> ModuleOutput:
        interp = _QUADRANT_INTERPRETATION.get(data.quadrant)
        if interp is None:
            return ModuleOutput(
                module_id=self.id, state=None, transition=None, strength=None,
                confidence=None, narrative="상대강도 데이터 없음(RRG 산정 불가).",
                inputs={"rs_ratio": data.rs_ratio, "rs_momentum": data.rs_momentum,
                        "quadrant": data.quadrant, "scope": "market_rs", "approximation": "single_window"},
            )
        state, transition, strength = interp
        return ModuleOutput(
            module_id=self.id, state=state, transition=transition, strength=strength,
            confidence=None, narrative=_QUADRANT_NARRATIVE[data.quadrant],
            inputs={"rs_ratio": data.rs_ratio, "rs_momentum": data.rs_momentum,
                    "quadrant": data.quadrant, "scope": "market_rs", "approximation": "single_window"},
        )
