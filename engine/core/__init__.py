"""engine.core — Engine Core 통일 계약의 공개 인터페이스.

정본: planning/blueprint_unified/00_architecture.md §4(Engine Core 통일 계약).

이 패키지가 export하는 타입들이 4단 tier(macro/sector/stock/strategy) 전체가
공유하는 "통일성의 본체"(§3, 계층 ②)다. 하위 tier는 이 모듈에서 import해
사용한다.
"""

from __future__ import annotations

from engine.core.contracts import (
    Direction,
    EngineOutput,
    ModuleOutput,
    Transition,
    Verdict,
)
from engine.core.context import Context
from engine.core.engine import Engine, Module
from engine.core.horizon import Horizon, map_macro_horizon
from engine.core.rulebook import Rulebook

__all__ = [
    "Horizon",
    "map_macro_horizon",
    "Transition",
    "Direction",
    "ModuleOutput",
    "Verdict",
    "EngineOutput",
    "Context",
    "Rulebook",
    "Module",
    "Engine",
]
