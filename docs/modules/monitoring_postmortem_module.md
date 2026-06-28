# 모듈: Monitoring & Postmortem

## 역할

전략 실행 후 결과를 모니터링하고, 리뷰와 postmortem을 통해 규칙을 개선한다.

## 현재 상태

상태: Planned.

## 현재 구현

- `/api/verification/{market}` scorecard 일부.
- 실제 거래 결과 저장, 리뷰, postmortem 모듈은 없다.

## 예정 입력

- 거래 내역.
- 포지션 변화.
- 전략 id.
- 시장/섹터/종목 verdict 변화.
- 손익과 drawdown.

## 예정 출력

- 전략별 성과 기록.
- 실패 원인.
- 개선 규칙.
- 반복 실수 태그.
- archive.

## 다음 개선

- trade journal schema.
- postmortem template.
- strategy outcome label.
