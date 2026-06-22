"""engine — 통합 4단 엔진 아키텍처(Macro -> Sector -> Stock -> Strategy)의 루트 패키지.

이 패키지는 `planning/blueprint_unified/00_architecture.md`(정본)에서 정의하는
Engine Core 통일 계약을 구현한다. 모든 tier(macro/sector/stock/strategy)는
`engine.core`가 정의하는 공용 타입(Module, Engine, Rulebook, Verdict,
ModuleOutput, Context, Horizon)을 통해서만 입출력한다.
"""
