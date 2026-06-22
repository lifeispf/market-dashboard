"""engine.macro — Stage 2 retrofit of the existing macro analysis onto Engine Core.

정본: planning/blueprint_unified/00_architecture.md §5(Macro 리트로핏 매핑).

이 패키지는 행동 변화 없이(byte-identical) 기존 backend/api/market.py의
_assemble_live 로직을 engine/core/의 Module/Rulebook/Engine 계약 위로
재배치한 것이다. 계산식은 scoring.py/scoring_ext.py를 그대로 호출한다 —
새로 발명한 계산은 없다.
"""
