# 5단계: 포트폴리오 의사결정 및 리밸런싱

## 목표

시장, 섹터, 종목 판단을 실제 포트폴리오 비중 결정으로 변환한다.

## 결정 범위

- 주식과 현금 비중.
- KOSPI와 NASDAQ 비중.
- 본주와 2배 레버리지 비중.
- 섹터별 투자 비중.
- 섹터 내 개별주/ETF 선택.

## 주요 입력

- Macro verdict.
- Sector verdict.
- Stock verdict.
- 현재 보유 종목과 비중.
- 목표 위험 수준.
- 계좌 제약 조건.

## 주요 출력

- 목표 현금 비중.
- 시장별 목표 비중.
- 레버리지 사용 여부와 비중.
- 섹터별 목표 비중.
- 종목/ETF별 후보 비중.

## 현재 구현 상태

상태: Partial.

DI-3 Action layer에서 종목별 entry, stop, weight hint 일부가 존재한다. 하지만 전체 포트폴리오 allocation engine은 아직 없다.

## 다음 구현

1. portfolio context 타입을 정의한다.
2. macro verdict를 현금/주식 비중으로 변환하는 보수적 룰부터 만든다.
3. sector verdict를 섹터 비중 cap/floor로 변환한다.
4. stock action hint를 실제 주문 계획이 아니라 목표 후보 비중으로 제한한다.
