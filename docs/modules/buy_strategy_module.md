# 모듈: Buy Strategy

## 역할

목표 포트폴리오와 현재 보유 현황의 차이를 바탕으로 매수/매도 계획을 수립한다.

## 현재 상태

상태: Planned.

## 예정 입력

- 현재 보유 종목과 수량.
- 평균단가.
- 목표 비중.
- 현금.
- 종목별 entry/stop/action hint.

## 예정 출력

- 리밸런싱 계획.
- 주문 후보.
- 분할 매수 계획.
- 실행 전 체크리스트.

## 다음 개선

- holdings input format.
- target/current diff 계산.
- paper plan output.
