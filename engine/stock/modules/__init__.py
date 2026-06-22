"""engine.stock.modules — 개별주 독립 관측 Module들.

현재 Price 레이어 2축만 구현: §35 Relative Strength(Market RS), §34 Price
Structure. 각 모듈은 Module 프로토콜을 만족하고 StockRow(data 인자)를 읽어
ModuleOutput을 산출한다. 결론은 rulebook.py가 낸다. §31 Quality / §32
Expectation / §33 Positioning / §36 Participation은 데이터 평면 이후로 연기.
"""
