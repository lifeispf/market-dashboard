"""engine/sector/modules/relative_strength.py — §21 Relative Strength Module.

정본: blueprint_micro/sector_engine/21_relative_strength.md (Sector Engine의 중심축).

기존 macro RRG 단일 윈도우 결과(SectorRow.rs_ratio/rs_momentum/quadrant,
scoring.py가 유일 출처)를 입력으로 받아 §21의 State/Transition 해석 레이어를
얹는다. 새 RRG 계산은 하지 않는다.

⚠️ 단일 윈도우 근사: 청사진 §21은 1M/3M/6M/12M 다중 시간축 동시 관찰을
요구하지만, 현 macro 엔진은 단일 윈도우(config.rrg)만 계산한다. 따라서 본
모듈은 단일 윈도우 quadrant에서 State/Transition을 도출하는 **근사**다 —
다중 시간축은 데이터 평면(§11 3단계) 확장 후 보강한다. 이 한계는 narrative와
inputs["approximation"]에 명시한다.

State 정량 경계(몇 %ile RS부터 Leader인가)는 90_open_questions.md D-12로 미해결 —
현재는 quadrant 기반 coarse 매핑이며 strength/confidence는 비검증 휴리스틱(§9.1).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import ModuleOutput
from engine.sector.classification import classify

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.sector.inputs import SectorRow

# RRG quadrant -> (State, Transition, coarse strength 0..1).
# quadrant 의미(scoring.rrg_quadrant, 100 중심):
#   leading   = 강RS + 강Momentum   -> 주도 지속
#   improving = 약RS + 강Momentum   -> 순환매 진입(차기 리더 후보)
#   weakening = 강RS + 약Momentum   -> 차익 임박(후반부)
#   lagging   = 약RS + 약Momentum   -> 소외
_QUADRANT_INTERPRETATION = {
    "leading": ("Leader", "Stable", 0.9),
    "improving": ("Emerging", "Improving", 0.65),
    "weakening": ("Leader", "Weakening", 0.5),
    "lagging": ("Lagging", "Stable", 0.2),
}

_QUADRANT_NARRATIVE = {
    "leading": "상대강도·모멘텀 모두 시장 우위 — 주도 지속(성숙 추세).",
    "improving": "상대강도는 아직 약하나 모멘텀이 시장을 앞선다 — 순환매 진입(차기 리더 후보).",
    "weakening": "상대강도는 높지만 모멘텀이 둔화 — 후반부, 차익 임박 경계.",
    "lagging": "상대강도·모멘텀 모두 시장 열위 — 소외.",
}


class SectorRelativeStrengthModule:
    """§21 — 섹터의 시장 대비 상대강도 관측(RRG 단일 윈도우 근사)."""

    id = "sector.relative_strength"
    tier = "sector"

    def available_for(self, market: str) -> bool:
        # RRG는 KOSPI/NASDAQ 양쪽에서 기존 데이터로 계산된다.
        return True

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        return []

    def compute(self, entity_id: str, ctx: "Context", data: "SectorRow") -> ModuleOutput:
        quadrant = data.quadrant
        interp = _QUADRANT_INTERPRETATION.get(quadrant)
        if interp is None:
            return ModuleOutput(
                module_id=self.id,
                state=None,  # quadrant 산정 불가 -> 우아한 degrade
                transition=None,
                strength=None,
                confidence=None,
                narrative="상대강도 데이터 없음(RRG 산정 불가).",
                inputs={
                    "rs_ratio": data.rs_ratio, "rs_momentum": data.rs_momentum,
                    "quadrant": quadrant, "approximation": "single_window",
                    "risk_profile": classify(entity_id),
                },
            )

        state, transition, strength = interp
        return ModuleOutput(
            module_id=self.id,
            state=state,
            transition=transition,
            strength=strength,
            confidence=None,  # 비검증 휴리스틱(§9.1) — 단일 윈도우 근사
            narrative=_QUADRANT_NARRATIVE[quadrant],
            inputs={
                "rs_ratio": data.rs_ratio, "rs_momentum": data.rs_momentum,
                "quadrant": quadrant, "approximation": "single_window",
                "risk_profile": classify(entity_id),
            },
        )
