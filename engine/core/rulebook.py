"""engine/core/rulebook.py — Rulebook 프로토콜(해석기).

정본: planning/blueprint_unified/00_architecture.md §4.2.

Rulebook은 ModuleOutput들을 해석해 단일 Verdict를 산출하는 역할만 한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.core.contracts import ModuleOutput, Verdict


@runtime_checkable
class Rulebook(Protocol):
    """해석기 — Module들의 ModuleOutput을 받아 Verdict를 산출한다.

    불변식 (00_architecture.md §4.2, "6축 합산 금지" 원칙의 코드 레벨 강제):
        Rulebook은 **fetch도 합산(평균)도 하지 않는다 — 패턴 매칭/거부권만
        한다.** 데이터를 가져오는 일은 Module의 책임이고, 점수를 평균 내
        합치는 일은 절대 하지 않는다 — 평균은 모듈 간 불일치(conflict) 정보를
        지워버리기 때문이다(§1.1 "6축 합산 금지", "불일치가 가장 중요한
        신호"). Rulebook이 할 수 있는 것은 오직: 패턴 매칭(예: 특정
        state/transition 조합 -> lead_pattern), 거부권(veto, 예: 한 모듈의
        breaking 상태가 전체 방향을 강제로 하향), 그리고 그 결과를 사람이
        읽을 수 있는 narrative/risks/invalidation으로 정리하는 것뿐이다.
    """

    def interpret(
        self, modules: "list[ModuleOutput]", upstream: "Context"
    ) -> "Verdict":
        """ModuleOutput 목록과 상위 컨텍스트를 해석해 Verdict를 산출한다.

        Args:
            modules: 이 tier의 Module들이 산출한 ModuleOutput 목록(이미
                available_for 필터를 통과한 것들).
            upstream: 상위 tier verdict들을 담은 Context(필터로 작용).

        Returns:
            패턴 매칭/거부권 적용 결과인 단일 Verdict. 절대 모듈 점수의
            평균이어서는 안 된다.
        """
        ...
