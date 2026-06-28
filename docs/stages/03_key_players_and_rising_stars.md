# 3단계: Key Player와 Rising Star 확인

## 목표

각 섹터 내에서 현재 주도주(Key Player)와 성장 후보(Rising Star)를 찾는다. 자동매매 관점에서는 섹터 판단을 실제 매수 후보군으로 좁히는 단계다.

## 주요 입력

- 섹터별 대표 구성종목.
- 개별 종목 가격 구조.
- 종목별 상대강도.
- 섹터 context.
- 수동 thesis와 risk 정보.

## 주요 출력

- 섹터별 Key Player 목록.
- 섹터별 Rising Star 목록.
- 종목별 verdict와 action hint.
- 후보 종목별 리스크와 무효화 조건.

## 현재 구현 상태

상태: Partial.

관련 파일:

- `backend/api/stocks.py`
- `engine/stock/engine.py`
- `engine/stock/action.py`
- `engine/stock/modules/price_structure.py`
- `engine/stock/modules/relative_strength.py`
- `engine/sector/constituents.py`
- `sectors.json`
- `frontend/src/components/StockView.tsx`
- `frontend/src/components/LeadershipSection.tsx`

## 미구현/불확실한 부분

- 종목 fundamental, expectation, positioning, participation, catalyst, risk 모듈이 충분히 구현되지 않았다.
- Key Player/Rising Star 분류 기준이 일부 수동 콘텐츠에 의존한다.
- action hint는 실제 주문 전략이 아니라 비검증 휴리스틱이다.

## 다음 구현

1. Key Player와 Rising Star의 정량/수동 기준을 분리한다.
2. stock engine의 각 모듈별 입력과 state를 문서화한다.
3. sector verdict가 stock conviction을 어떻게 보정하는지 테스트한다.
