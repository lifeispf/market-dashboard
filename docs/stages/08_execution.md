# 8단계: 매수전략 실행

## 목표

수립된 매매 전략을 관리하고 실행한다. 최종 자동매매 시스템에서는 브로커 API와 연결될 수 있다.

## 주요 입력

- 승인된 매매 계획.
- 계좌 상태.
- 주문 가능 금액.
- 실시간 또는 준실시간 가격.
- 리스크 제한.

## 주요 출력

- 주문 요청.
- 주문 상태.
- 체결 결과.
- 실패/취소 기록.

## 현재 구현 상태

상태: Planned.

현재 브로커 API 연동, 주문 실행, 자동매매 실행 모듈은 없다.

## 안전 원칙

- 실행 계층은 검증 게이트 통과 전 구현하지 않는다.
- paper trading 또는 simulation 계층을 먼저 만든다.
- 실제 주문 전에는 kill switch, max loss, max position, duplicate order 방지 장치가 필요하다.

## 다음 구현

1. paper trading execution interface부터 설계한다.
2. 주문 실행 전 승인/검증 gate를 만든다.
3. 실제 broker adapter는 가장 마지막에 연결한다.
