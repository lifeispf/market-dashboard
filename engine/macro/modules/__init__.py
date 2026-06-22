"""engine.macro.modules — S01~S06 + fear_greed 독립 관측 Module들.

각 모듈은 engine/core/engine.py의 Module 프로토콜을 만족하고 MacroInputs를
data 인자로 받아 ModuleOutput을 산출한다. 결론(direction 등)은 내리지
않는다 — 그건 engine/macro/rulebook.py의 책임이다.
"""
