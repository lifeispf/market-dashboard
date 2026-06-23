"""engine/verification/ — Phase F 검증 레이어(스코어카드 v1).

planning/elegant-soaring-twilight.md Phase F. 백필된 series_daily(5년)에서
백테스트 가능한 부분집합 신호를 과거 시점마다 재구성하고 forward-return과
상관(IC)·hit-rate를 산출한다. manual/KRX 팩터(S02/S03/S04)는 과거 데이터가
없어 명시적으로 제외한다. 보호 파일(scoring.py 등)은 호출만 한다.
"""
