# 9단계: 모니터링, 리뷰, Postmortem

## 목표

매수 후 결과를 모니터링하고, 전략을 수정하며, 반복되는 실수를 줄이기 위한 기록 체계를 만든다.

## 주요 입력

- 체결 결과.
- 보유 포지션.
- 시장/섹터/종목 verdict 변화.
- 손익과 drawdown.
- 전략별 결과.

## 주요 출력

- 리밸런싱 필요 여부.
- 전략 수정 제안.
- postmortem 기록.
- 실수/개선점 아카이브.
- 다음 전략 rule 개선안.

## 현재 구현 상태

상태: Planned.

현재 `/api/verification/{market}` scorecard 일부는 있으나, 실제 매매 결과 리뷰나 postmortem 저장소는 없다.

## 다음 구현

1. trade journal schema를 만든다.
2. 전략 id와 결과를 연결한다.
3. 반복 실수를 태깅하고 rulebook 개선 이슈로 전환한다.
