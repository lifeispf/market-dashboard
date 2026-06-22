"""engine/core/engine.py — Module 프로토콜 + Engine 실행기.

정본: planning/blueprint_unified/00_architecture.md §4.2(Module/Engine).

Module은 독립 observer(관측만, 결론 금지)이고, Engine은 한 tier(모듈 N개 +
Rulebook 1개)를 실행하는 오케스트레이터다. Engine.run()의 절차는 §4.2의
의사코드를 정확히 따른다:
    1. available_for(ctx.market)가 True인 모듈만 compute -> outs
    2. rulebook.interpret(outs, ctx) -> verdict
    3. mode 결정(live/mock/degraded)
    4. EngineOutput 조립 및 반환
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from engine.core.contracts import EngineOutput

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.core.contracts import ModuleOutput
    from engine.core.rulebook import Rulebook


@runtime_checkable
class Module(Protocol):
    """독립 observer — 한 가지 질문만 본다.

    불변식 (00_architecture.md §4.2): Module은 **fetch/관측만 하고 결론을
    내리지 않는다.** state/transition/strength/confidence를 산출할 수는
    있지만, 그것들을 종합해 direction이나 risks 같은 "해석"을 내리는 일은
    Rulebook의 책임이다. 이 분리가 "6축 합산 금지" 원칙을 코드 레벨에서
    강제한다.

    Attributes:
        id: 모듈 식별자(예: "macro.S01").
        tier: 이 모듈이 속한 tier("macro" | "sector" | "stock" | "strategy").
    """

    id: str
    tier: str

    def available_for(self, market: str) -> bool:
        """이 모듈이 주어진 market에서 사용 가능한지 여부.

        00_architecture.md §9.4: 한국 미지원 모듈(예: 13F/FINRA 기반)은
        False를 반환해 정직하게 빠진다 — 가짜값으로 메우지 않는다.
        """
        ...

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        """이 모듈이 compute()에 필요로 하는 데이터 시리즈 id 목록.

        데이터 평면(engine/data/)의 prefetch에 사용된다.
        """
        ...

    def compute(self, entity_id: str, ctx: "Context", data: Any) -> "ModuleOutput":
        """관측을 수행해 ModuleOutput을 산출한다. 결론(direction 등)은 내리지 않는다."""
        ...


@dataclass
class Engine:
    """tier 1개 = 모듈 N개 + Rulebook 1개.

    Attributes:
        tier: 이 Engine이 담당하는 tier명("macro" | "sector" | "stock" |
            "strategy").
        modules: 이 tier를 구성하는 Module 목록.
        rulebook: 이 tier의 ModuleOutput들을 해석해 Verdict를 산출하는
            Rulebook.
    """

    tier: str
    modules: list[Module] = field(default_factory=list)
    rulebook: "Rulebook | None" = None

    def run(self, entity_id: str, ctx: "Context", data: Any) -> EngineOutput:
        """이 tier를 실행해 EngineOutput을 산출한다.

        절차(00_architecture.md §4.2):
            1. available_for(ctx.market)가 True인 모듈만 compute() 호출.
            2. rulebook.interpret(outs, ctx)로 Verdict 산출.
            3. mode 결정: outs 중 state 또는 confidence가 None인 모듈이
               하나라도 있으면 "degraded", 아니면 "live"를 기본으로 한다.
               (TODO: data 인자가 "mock" 데이터 소스임을 나타내는 경우
               mode="mock"으로 분기하는 규칙은 §11 마이그레이션 2단계
               이후 data 평면 계약이 확정되면 추가한다. 지금은 mock 판별
               기준이 없으므로 live/degraded 둘만 결정한다.)
            4. EngineOutput(tier, entity_id, verdict, modules=outs,
               context=ctx.as_dict(), freshness=[], mode) 반환.

        Args:
            entity_id: macro -> market, sector -> code, stock -> ticker.
            ctx: 상위 tier verdict들을 담은 Context.
            data: 데이터 평면에서 가져온 원시 데이터(이 단계에서는 형태를
                규정하지 않는다 — Module.compute()가 해석한다).

        Returns:
            이 tier 실행의 전체 결과(EngineOutput).
        """
        outs: list["ModuleOutput"] = [
            m.compute(entity_id, ctx, data)
            for m in self.modules
            if m.available_for(ctx.market)
        ]

        verdict = self.rulebook.interpret(outs, ctx)

        degraded = any(o.state is None or o.confidence is None for o in outs)
        mode: str = "degraded" if degraded else "live"

        return EngineOutput(
            tier=self.tier,
            entity_id=entity_id,
            verdict=verdict,
            modules=outs,
            context=ctx.as_dict(),
            freshness=[],
            mode=mode,  # type: ignore[arg-type]
        )
