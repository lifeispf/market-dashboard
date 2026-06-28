# 검증과 안전 정책

작성 기준일: 2026-06-28

## 원칙

자동매매 시스템으로 확장하려면 검증되지 않은 판단과 실제 주문 실행 사이에 명확한 안전 장벽이 있어야 한다.

## 현재 정책

- 검증 전 확률, 승률, 수익률 기대값을 사용자에게 노출하지 않는다.
- `conviction` 또는 `strength`는 확률이 아니라 rule alignment 또는 ranking signal로 취급한다.
- 실제 주문 실행은 현재 범위 밖이다.
- action hint는 매수/매도 지시가 아니라 연구용 계획 후보로 표시한다.

## 상태 구분

| 상태 | 의미 | UI/문서 표현 |
|---|---|---|
| Unvalidated | 룰은 있으나 과거 검증 없음 | 비검증 휴리스틱 |
| Fixture-tested | synthetic/fixture 테스트 통과 | 계산 동작 확인 |
| Historical-tested | 과거 데이터 검증 일부 통과 | 제한적 신뢰 |
| Calibrated | 확률/강도 보정 완료 | 확률 표현 가능 후보 |
| Paper-tested | 모의매매 통과 | 실행 후보 |
| Live-approved | 실거래 승인 | 실제 주문 가능 |

현재 대부분의 판단은 `Unvalidated` 또는 `Fixture-tested` 수준이다.

## 자동매매 전 필수 게이트

1. API contract와 데이터 freshness가 안정적이어야 한다.
2. 각 signal의 forward return 또는 hit-rate가 검증되어야 한다.
3. false positive/false negative 분석이 있어야 한다.
4. paper trading 결과가 있어야 한다.
5. 손실 제한, 중복 주문 방지, kill switch가 있어야 한다.
6. postmortem 기록 체계가 있어야 한다.

## 금지 표현

- 매수하세요.
- 확실히 오릅니다.
- 승률이 보장됩니다.
- 상승 확률 70%입니다. 단, calibration 전.

## 허용 표현

- 리서치 관점에서 강세가 확인됩니다.
- 현재 룰 정렬 기준으로 우호적입니다.
- 이 판단은 다음 조건에서 무효화됩니다.
- 검증 전 휴리스틱이며 자동 주문 신호가 아닙니다.

## 현재 필요한 검증

| 영역 | 필요한 검증 |
|---|---|
| Macro regime | 레짐별 forward return, drawdown |
| Sector RRG | quadrant별 hit-rate와 rotation persistence |
| Stock RS/price structure | 후보군 forward excess return |
| Action hint | entry/stop/weight rule의 paper trading |
| Portfolio allocation | 현금/레버리지 비중별 성과와 리스크 |
