# 1단계: 증시 모멘텀과 상황 확인

## 목표

KOSPI와 NASDAQ의 전체 시장 환경을 판단한다. 자동매매 관점에서는 시장별 투자 가능성, 현금 비중, 레버리지 사용 가능성을 결정하는 상위 필터 역할을 한다.

## 주요 입력

- 지수 레벨, 변화율, 히스토리.
- 유동성 6축 지표.
- 변동성 지표.
- 수급과 breadth.
- 밸류에이션과 ceiling.
- 공포탐욕 지표.

## 주요 출력

- 시장별 레짐.
- 위험 선호/위험 회피 판단.
- 주요 리스크와 무효화 조건.
- 시장별 briefing summary.
- 하위 섹터/종목 판단에 전달할 context.

## 현재 구현 상태

상태: Partial, Operational.

관련 파일:

- `backend/api/market.py`
- `backend/api/briefing.py`
- `engine/macro/`
- `engine/cascade.py`
- `scoring.py`
- `frontend/src/components/GlobalMacroBar.tsx`
- `frontend/src/components/ExecutiveSummary.tsx`

## 미구현/불확실한 부분

- 모든 레짐 판단이 충분히 검증된 것은 아니다.
- market verdict가 실제 포트폴리오 현금/레버리지 비중으로 직접 연결되지는 않는다.
- action layer와 portfolio layer 사이의 계약이 아직 없다.

## 다음 구현

1. macro verdict를 portfolio allocation 입력으로 표준화한다.
2. `/api/briefing`의 macro output에 검증 상태와 data freshness를 더 명확히 노출한다.
3. historical validation을 통해 레짐별 forward return 분포를 문서화한다.
