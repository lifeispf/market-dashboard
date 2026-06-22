"""engine/macro/rulebook.py — MacroRulebook.

00_architecture.md §5 매핑: `composite_score` + `regime_from_score` +
`reconciliation_status`(scoring.py) -> Verdict. 이 단계의 목적은
byte-identical 보존이므로, Verdict는 기존 macro의 정의된 합성(composite_score)
결과를 "담는 그릇"이다 -- 새로운 해석을 발명하지 않는다.

설계 노트 -- 왜 MacroRulebook이 MacroInputs를 생성자로 받는가:
    engine/core/rulebook.py의 Rulebook 프로토콜은 `interpret(modules, upstream)`
    두 인자만 받는다(Context에는 composite/regime/recon 같은 macro 전용 raw
    계산 결과를 실을 자리가 없다 -- Context는 4-tier 공용 캐스케이드 필터일
    뿐이다). composite/regime/reconciliation은 모듈별로 쪼개지지 않는 macro
    tier 전체의 합성값이라, "modules의 inputs["raw_score"]에서 모아 다시
    계산"하는 경로도 가능하지만 reconciliation_status가 필요로 하는
    `position`(가격밴드, 지수 밸류에이션 -- 어느 S0X 모듈에도 속하지 않는
    값)은 모듈 출력에 없다. 따라서 MacroRulebook은 같은 data 소스
    (MacroInputs)를 생성자로 직접 받아 Module들과 "같은 원천을 본다" --
    Rulebook 프로토콜의 interpret() 시그니처는 그대로 지키면서, fetch는 전혀
    하지 않고(gather_macro_inputs가 이미 다 채워둔 값을 읽기만 함) 오직
    해석(패턴 매칭: regime -> direction)만 한다. 평균은 내지 않는다 --
    scoring.composite_score 자체가 가중합이며 이는 기존 macro가 1단계부터
    정의해 온 합성이다("6축 단순평균 금지"는 *이걸 대체하는 새 평균을 만들지
    말라*는 뜻 -- 기존 동작 보존이 최우선이므로 그대로 재사용한다).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import Verdict

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.core.contracts import ModuleOutput
    from engine.macro.inputs import MacroInputs

REGIME_LABEL = {
    "base": "BASE only — 멀티플 유지가 한계",
    "bull": "BULL 도달가능 — 재평가 연료 부분충전",
    "hyper": "HYPER 연료 존재 — 지속가능성은 별도 경고",
}

# regime("base"/"bull"/"hyper") -> Direction. None(regime 산정 불가) -> "neutral".
_REGIME_TO_DIRECTION = {"base": "neutral", "bull": "up", "hyper": "strong_up"}

# Direction -> 0..4 strength (Verdict.strength contract: int 0..4).
_DIRECTION_STRENGTH = {
    "strong_down": 4, "down": 3, "neutral": 2, "up": 3, "strong_up": 4,
}


class MacroRulebook:
    """macro tier 해석기 -- composite/regime/reconciliation을 호출만 한다
    (평균을 내지 않음, scoring.composite_score가 이미 가중합을 수행).

    Args:
        inputs: 이 실행의 MacroInputs(engine/macro/engine.py가 Module들과
            정확히 같은 인스턴스를 전달한다). None이면 우아하게 degrade한
            neutral Verdict를 반환한다(절대 크래시하지 않음).
    """

    def __init__(self, inputs: "MacroInputs | None" = None) -> None:
        self._inputs = inputs

    def interpret(self, modules: "list[ModuleOutput]", upstream: "Context") -> Verdict:
        data = self._inputs

        if data is None:
            return Verdict(
                direction="neutral",
                strength=0,
                conviction=None,
                lead_pattern=None,
                narrative="macro inputs unavailable",
                risks=["no_data"],
                invalidation=[],
                horizon="T0",
                verified=False,
                extra={},
            )

        regime = data.regime
        composite = data.composite
        recon = data.recon

        direction = _REGIME_TO_DIRECTION.get(regime, "neutral")
        strength = _DIRECTION_STRENGTH.get(direction, 2)

        narrative = REGIME_LABEL.get(regime, "산정 불가") if regime else "산정 불가"

        return Verdict(
            direction=direction,
            strength=strength,
            conviction=None,  # macro는 비검증 휴리스틱 영역 -- 임의 conviction 금지
            lead_pattern=regime,
            narrative=narrative,
            risks=[],
            invalidation=[],
            horizon="T1",
            verified=False,
            extra={
                "composite": composite,
                "n_avail": data.n_avail,
                "n_total": data.n_total,
                "regime": regime,
                "reconciliation": recon,
                "supportedCeiling": data.supported_ceiling,
                "position": data.position,
                "levels": data.levels,
                "fear_greed": data.fear_greed,
            },
        )
