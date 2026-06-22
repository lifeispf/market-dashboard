"""engine.sector.modules — 섹터 독립 관측 Module들.

현재 §21 Relative Strength(중심축)만 구현. 각 모듈은 engine/core/engine.py의
Module 프로토콜을 만족하고 SectorRow(data 인자)에서 값을 읽어 ModuleOutput을
산출한다. 결론(direction 등)은 내리지 않는다 — rulebook.py의 책임이다.
"""
