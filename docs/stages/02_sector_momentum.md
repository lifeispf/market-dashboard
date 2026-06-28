# 2단계: 섹터별 모멘텀과 상황 확인

## 목표

KOSPI와 NASDAQ 내부에서 어떤 섹터가 현재 주도하고 있고, 어떤 섹터가 다음 후보이며, 어떤 섹터가 약화되고 있는지 판단한다.

## 주요 입력

- 섹터 ETF 또는 섹터 대표 지수 가격.
- 벤치마크 대비 상대강도.
- RS Ratio, RS Momentum.
- RRG quadrant.
- 섹터 내부 concentration과 breadth.
- 상위 macro context.

## 주요 출력

- 섹터별 direction, strength, conviction.
- Leading, Improving, Weakening, Lagging 분류.
- 섹터별 narrative, risks, invalidation.
- 섹터별 투자 비중 결정을 위한 rank/context.

## 현재 구현 상태

상태: Partial.

관련 파일:

- `backend/api/sectors.py`
- `engine/sector/engine.py`
- `engine/sector/rulebook.py`
- `engine/sector/modules/relative_strength.py`
- `engine/sector/concentration.py`
- `frontend/src/components/SectorView.tsx`
- `frontend/src/components/RRGChart.tsx`

## 미구현/불확실한 부분

- breadth, participation, catalyst, rotation 모듈은 아직 완전하지 않다.
- 섹터별 실제 투자 비중 산식은 아직 없다.
- KOSPI 섹터 매핑과 NASDAQ ETF 구성종목 기준이 완전히 동일하지 않다.

## 다음 구현

1. sector module별 상태 계약을 문서화한다.
2. breadth/participation/catalyst 모듈을 단계적으로 구현한다.
3. sector verdict를 portfolio allocation layer로 넘기는 인터페이스를 만든다.
