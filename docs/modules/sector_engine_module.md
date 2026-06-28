# 모듈: Sector Engine

## 역할

시장 내부의 섹터별 주도, 후보, 약화, 위험 상태를 판단한다.

## 현재 상태

상태: Partial, Tested 일부.

## 주요 파일

- `backend/api/sectors.py`
- `engine/sector/engine.py`
- `engine/sector/rulebook.py`
- `engine/sector/modules/relative_strength.py`
- `engine/sector/concentration.py`
- `engine/sector/constituents.py`

## 입력

- 시장 context.
- 섹터 가격/수익률.
- 벤치마크 대비 상대강도.
- RRG 지표.
- 구성종목/market cap/거래대금 일부.

## 출력

- sector `EngineOutput[]`.
- sector verdict.
- RRG quadrant.
- concentration.
- constituents.
- narrative, risks, invalidation.

## 한계

- breadth, participation, catalyst, rotation 모듈은 아직 부분적이거나 미구현이다.
- KOSPI와 NASDAQ 데이터 소스가 완전히 대칭적이지 않다.
- sector verdict가 portfolio weight로 변환되는 계약은 아직 없다.

## 다음 개선

- sector module별 `ModuleOutput` 계약 고정.
- breadth/participation/catalyst 구현.
- sector allocation input 계약 작성.
