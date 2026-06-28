# 모듈: Portfolio Decision

## 역할

시장, 섹터, 종목 판단을 포트폴리오 비중 결정으로 변환한다.

## 현재 상태

상태: Partial.

## 현재 구현

- stock action hint에 weight 관련 정보 일부가 존재한다.
- 전체 포트폴리오 allocation engine은 없다.

## 예정 입력

- Macro verdict.
- Sector verdict.
- Stock verdict.
- 현재 보유 현황.
- 목표 위험 수준.
- 계좌 제약 조건.

## 예정 출력

- 현금/주식 비중.
- KOSPI/NASDAQ 비중.
- 본주/2배 레버리지 비중.
- 섹터별 목표 비중.
- 종목/ETF별 목표 비중.

## 다음 개선

- portfolio context schema.
- macro→cash/equity allocation rule.
- sector→sector weight rule.
- stock→candidate weight rule.
