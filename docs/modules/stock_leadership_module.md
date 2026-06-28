# 모듈: Stock Leadership

## 역할

섹터 내 Key Player와 Rising Star를 식별하고, 종목별 price/RS 기반 판단과 action hint를 제공한다.

## 현재 상태

상태: Partial, Tested 일부.

## 주요 파일

- `backend/api/stocks.py`
- `engine/stock/engine.py`
- `engine/stock/action.py`
- `engine/stock/modules/price_structure.py`
- `engine/stock/modules/relative_strength.py`
- `sectors.json`
- `frontend/src/components/StockView.tsx`

## 입력

- sector context.
- 종목 가격/수익률.
- 종목 상대강도.
- 수동 thesis/risk.
- 섹터 구성종목.

## 출력

- stock `EngineOutput[]`.
- price structure state.
- relative strength state.
- action levels: entry, stop, weight hint.
- narrative, risks, invalidation.

## 한계

- fundamental, expectation, positioning, participation, catalyst, risk 모듈은 아직 충분하지 않다.
- action hint는 자동 주문 지시가 아니다.
- 검증 전이므로 확률/승률로 해석하면 안 된다.

## 다음 개선

- Key Player/Rising Star 분류 기준 문서화.
- stock action hint의 입력/출력 계약 테스트.
- chart strategy module 설계.
