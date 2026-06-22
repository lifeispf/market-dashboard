"""engine.sector — Stage 4 retrofit of sector analysis onto Engine Core.

정본: planning/blueprint_unified/00_architecture.md §4/§11,
blueprint_micro/sector_engine/.

기존 macro 경로(backend/api/market.py:_assemble_sectors_leaders)가 절차적으로
계산하던 섹터 RRG metric을 Engine Core(Module/Rulebook/Engine) 위로 재배치한다.
RRG 원시 계산(rs_ratio/rs_momentum/quadrant)은 scoring.py를 유일 출처로 재사용
하고(§21 데이터 계약, 2026-06-21 결정), Sector Engine은 그 위에 State/Transition/
Verdict 해석 레이어만 얹는다 — 같은 공식을 두 번 구현하지 않는다.

이 단계 범위: §21 Relative Strength(중심축)만 구현. §22 Breadth / §23
Participation / §24 Rotation / §25 Momentum / §26 Catalyst는 섹터 단위 데이터가
데이터 평면(§11 3단계)에서 들어온 뒤 추가한다 — 그 전까지는 graceful degrade.
"""
