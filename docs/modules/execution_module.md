# 모듈: Execution

## 역할

승인된 매매 전략을 실제 또는 모의 주문으로 실행한다.

## 현재 상태

상태: Planned.

## 예정 입력

- 승인된 매매 계획.
- 계좌 상태.
- 브로커 API adapter.
- 리스크 제한.

## 예정 출력

- 주문 요청.
- 주문 상태.
- 체결 결과.
- 실패/취소 로그.

## 안전 요구사항

- paper trading 우선.
- kill switch.
- duplicate order 방지.
- max loss, max exposure 제한.
- 실제 주문 전 별도 승인 게이트.

## 다음 개선

- execution interface 초안.
- paper broker adapter.
- order lifecycle schema.
