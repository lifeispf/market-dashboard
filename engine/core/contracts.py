"""engine/core/contracts.py — Engine Core 통일 계약의 핵심 데이터 타입.

정본: planning/blueprint_unified/00_architecture.md §4.1.

모든 tier(macro/sector/stock/strategy)가 동일한 모양으로 입출력하는 3개의
dataclass(ModuleOutput, Verdict, EngineOutput)와 그 보조 Literal 타입
(Transition, Direction)을 정의한다. 이 모듈이 틀리면 하위 모든 tier가
틀린다 — 필드명/타입은 §4.1을 정확히 따른다.

설계 원칙(00_architecture.md §1.1):
    - 6축 합산 금지: ModuleOutput은 결론을 내리지 않는 독립 관측이다.
    - 우아한 degrade: state/transition/strength/confidence는 전부
      Optional이다 — 데이터 미가용은 None, 크래시·임의값 금지.
    - 검증 게이트 1급 시민: Verdict.verified는 walk-forward 통과 전까지
      항상 False로 취급한다(§9.1).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from engine.core.horizon import Horizon

Transition = Literal["improving", "stable", "weakening", "breaking"]
"""모듈 관측의 추세 전환 상태(00_architecture.md §4.1)."""

Direction = Literal["strong_up", "up", "neutral", "down", "strong_down"]
"""Rulebook이 산출하는 최종 방향(00_architecture.md §4.1)."""


@dataclass
class ModuleOutput:
    """독립 관측기(Module) 1개의 산출 — 결론을 내리지 않는다.

    Attributes:
        module_id: 모듈 식별자. 예: "macro.S01" | "sector.relative_strength"
            | "stock.quality".
        state: tier별 어휘로 표현된 관측 상태(예: 매크로 regime의
            base/bull/hyper, 섹터의 Leading/Improving/...). None은
            unknown(우아한 degrade) — 데이터 미가용을 의미하며 크래시나
            임의값으로 메우지 않는다.
        transition: 추세 전환 상태. 관측 불가 시 None.
        strength: 0..1로 정규화된 강도. macro의 0~100 점수는 /100으로
            정규화해 채운다. 관측 불가 시 None.
        confidence: 비검증 휴리스틱(00_architecture.md §9.1). walk-forward
            검증 전까지는 "랭킹 신호"로만 취급한다. 관측 불가 시 None.
        narrative: 이 모듈 관측에 대한 사람이 읽을 수 있는 서술.
        inputs: 드릴다운/freshness용 원시값 보존. 기본값은 빈 dict.
    """

    module_id: str
    state: str | None
    transition: Transition | None
    strength: float | None
    confidence: float | None
    narrative: str
    inputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """이 ModuleOutput을 JSON 직렬화 가능한 dict로 변환한다."""
        return asdict(self)


@dataclass
class Verdict:
    """Rulebook 산출 — 모든 tier가 동일한 모양으로 만드는 최종 해석.

    Attributes:
        direction: 최종 방향(Direction).
        strength: 0..4 정수 강도.
        conviction: 비검증 휴리스틱(§9.1). None 허용(우아한 degrade).
        lead_pattern: 매칭된 패턴 이름. 예: "Strong Leader" | "Value Trap"
            | "Early Rotation". 매칭 없으면 None.
        narrative: 이 Verdict에 대한 사람이 읽을 수 있는 서술.
        risks: 식별된 리스크 목록. 기본값은 빈 list.
        invalidation: 이 Verdict가 무효화되는 조건 목록. 기본값은 빈 list.
        horizon: 이 Verdict가 적용되는 정규 Horizon.
        verified: walk-forward 검증 통과 여부. 검증 전까지는 항상 False —
            §9.1의 expose_only_if_backtested 게이트.
        extra: tier별 확장 필드(stock: position_size_hint / macro:
            supportedCeiling, reconciliation 등). 기본값은 빈 dict.
    """

    direction: Direction
    strength: int
    conviction: float | None
    lead_pattern: str | None
    narrative: str
    risks: list[str] = field(default_factory=list)
    invalidation: list[str] = field(default_factory=list)
    horizon: Horizon = "T0"
    verified: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """이 Verdict를 JSON 직렬화 가능한 dict로 변환한다."""
        return asdict(self)


@dataclass
class EngineOutput:
    """한 tier 실행의 전체 결과 — API envelope의 원형(00_architecture.md §7.2).

    Attributes:
        tier: "macro" | "sector" | "stock" | "strategy".
        entity_id: macro -> market, sector -> code, stock -> ticker.
        verdict: 이 tier의 Rulebook이 산출한 최종 Verdict.
        modules: 이 tier를 구성한 모든 ModuleOutput. 기본값은 빈 list.
        context: 나를 필터한 상위 tier verdict들의 직렬화(Context.as_dict()).
        freshness: 기존 freshness 계승. 기본값은 빈 list.
        mode: "live" | "mock" | "degraded".
    """

    tier: str
    entity_id: str
    verdict: Verdict
    modules: list[ModuleOutput] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    freshness: list[dict[str, Any]] = field(default_factory=list)
    mode: Literal["live", "mock", "degraded"] = "live"

    def to_dict(self) -> dict[str, Any]:
        """이 EngineOutput을 중첩 dataclass까지 재귀 직렬화한 dict로 변환한다.

        verdict/modules가 dataclass(또는 dataclass 리스트)이므로
        `dataclasses.asdict`가 재귀적으로 펼친다 — API envelope 직렬화의
        원형이다.
        """
        return asdict(self)
