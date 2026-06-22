"""engine/core/context.py — 캐스케이드 컨텍스트(상위 tier verdict의 전달체).

정본: planning/blueprint_unified/00_architecture.md §4.3(캐스케이드).

"상위 verdict가 하위의 context(필터)가 된다"는 캐스케이드 원칙(§4.3)을
구현한다. Context는 캐스케이드 체인을 따라 흐르며, 각 tier가 실행될 때마다
자신의 verdict를 upstream에 추가해 다음 tier로 넘긴다 — 체인 전체(예:
macro+sector)가 보존되어야 하위 tier(stock)가 macro 맥락까지 볼 수 있다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from engine.core.horizon import Horizon

if TYPE_CHECKING:
    from engine.core.contracts import EngineOutput, Verdict


@dataclass
class Context:
    """현재 tier 실행을 필터하는 상위 tier verdict들의 모음.

    Attributes:
        market: 시장 식별자(예: "KOSPI" | "NASDAQ").
        upstream: 상위 tier명 -> 그 tier의 Verdict. 예:
            {"macro": <Verdict>, "sector": <Verdict>}. 루트 컨텍스트는
            빈 dict.
        horizon: 이 컨텍스트가 가리키는 정규 Horizon. 지정 없으면 None.
    """

    market: str
    upstream: dict[str, "Verdict"] = field(default_factory=dict)
    horizon: Horizon | None = None

    @classmethod
    def root(cls, market: str) -> "Context":
        """캐스케이드 최상위(macro) 실행을 위한 루트 컨텍스트.

        upstream이 비어 있다 — macro에는 더 상위 tier가 없다.
        """
        return cls(market=market, upstream={})

    @classmethod
    def from_macro(cls, macro: "EngineOutput") -> "Context":
        """macro EngineOutput으로부터 sector tier용 Context를 만든다.

        upstream={"macro": macro.verdict}. market은 macro.entity_id를
        그대로 따른다(macro의 entity_id == market).
        """
        return cls(market=macro.entity_id, upstream={"macro": macro.verdict})

    @classmethod
    def from_sector(cls, sector: "EngineOutput", base: "Context") -> "Context":
        """sector EngineOutput과 base Context로부터 stock tier용 Context를 만든다.

        base.upstream(macro 포함)을 보존한 채 "sector": sector.verdict를
        추가한다 — 캐스케이드 체인 전체(macro+sector)가 유지되어야
        00_architecture.md §4.3의 "상위 맥락이 하위 필터로 흘러간다"는
        원칙이 성립한다.
        """
        merged_upstream = dict(base.upstream)
        merged_upstream["sector"] = sector.verdict
        return cls(market=base.market, upstream=merged_upstream, horizon=base.horizon)

    def as_dict(self) -> dict[str, Any]:
        """이 Context를 직렬화한다 — upstream의 각 Verdict는 to_dict()로 펼친다."""
        return {
            "market": self.market,
            "upstream": {
                tier: verdict.to_dict() for tier, verdict in self.upstream.items()
            },
            "horizon": self.horizon,
        }
