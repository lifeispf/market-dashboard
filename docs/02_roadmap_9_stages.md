# 9단계 로드맵

작성 기준일: 2026-06-28

이 문서는 자동매매 시스템까지 가기 위한 전체 기능 범위를 9단계로 정의한다. 현재 구현은 일부 단계에만 걸쳐 있으며, 구현된 부분도 모두 검증된 것은 아니다.

## 전체 단계 요약

| 단계 | 이름 | 목표 | 현재 상태 |
|---:|---|---|---|
| 1 | 증시 모멘텀/상황 확인 | KOSPI/NASDAQ 전체 환경 판단 | Partial, Operational |
| 2 | 섹터 모멘텀/상황 확인 | 시장 내 섹터별 주도/후보/위험 판단 | Partial |
| 3 | Key Player/Rising Star 확인 | 섹터 내 주도주와 성장주 후보 식별 | Partial |
| 4 | 주요 이벤트 확인 | 매크로/정부/산업/기업 이벤트 추적 | Planned |
| 5 | 포트폴리오 의사결정/리밸런싱 | 현금/시장/섹터/종목 비중 결정 | Partial |
| 6 | 매수 전략 수립 | 보유 현황과 목표 기반 리밸런싱 전략 | Planned |
| 7 | 개별주 이벤트/차트 기반 전략 | 종목별 체크아웃 지표, 진입/손절 구체화 | Planned |
| 8 | 매수전략 실행 | 개별주/ETF 매매 전략 관리 및 실행 | Planned |
| 9 | 모니터링/리뷰/postmortem | 결과 리뷰, 규칙 개선, 실수 방지 | Planned |

## 1단계: 증시 모멘텀과 상황 확인

목표:

- KOSPI와 NASDAQ의 전체 시장 상태를 판단한다.
- 유동성, 수급, 변동성, 밸류에이션, breadth, 레짐을 종합하되 단일 평균 점수에 과의존하지 않는다.

현재 구현:

- `/api/market/{market}` frozen market payload.
- `/api/briefing/{market}` macro cascade summary.
- `engine/macro/`, `scoring.py`, `backend/api/market.py`.
- GitHub Actions가 payload를 생성해 Cloudflare KV에 업로드.

상태: Partial, Operational.

## 2단계: 섹터별 모멘텀과 상황 확인

목표:

- 각 시장 내 섹터별 상대강도, 모멘텀, RRG quadrant, concentration, leadership breadth를 판단한다.

현재 구현:

- `/api/sectors/{market}`.
- `engine/sector/`, `engine/sector/modules/relative_strength.py`.
- multi-window RRG와 concentration 일부.

상태: Partial.

## 3단계: Key Player와 Rising Star 확인

목표:

- 섹터별 Key Player와 Rising Star를 확인한다.
- 섹터 ETF 구성종목 또는 KRX 매핑 기반으로 주도 종목을 확장한다.

현재 구현:

- `/api/stocks/{market}`.
- `engine/stock/`, `engine/stock/modules/price_structure.py`, `relative_strength.py`.
- `sectors.json` 기반 leaders와 `engine/sector/constituents.py`.

상태: Partial.

## 4단계: 주요 이벤트 확인

목표:

- 연준 관련 이벤트.
- 주요 지표 발표 이벤트.
- 미국 정부 관련 이벤트.
- 한국 정부 관련 이벤트.
- 주요 산업/기업 관련 이벤트.

현재 구현:

- 독립 이벤트 캘린더/이벤트 rulebook은 아직 없다.
- 일부 macro/stock narrative와 watchlist에 이벤트성 표현이 섞여 있을 수 있으나, 구조화된 모듈은 아니다.

상태: Planned.

## 5단계: 포트폴리오 의사결정 및 리밸런싱

목표:

- 전체 증시 상황을 고려해 주식/현금 비중을 결정한다.
- KOSPI/NASDAQ 비중을 결정한다.
- 본주와 2배 레버리지 비중을 결정한다.
- 섹터별 투자 비중을 결정한다.
- 섹터 내 투자할 개별주 및 ETF를 결정한다.

현재 구현:

- DI-3 Action layer가 일부 종목별 entry, stop, weight hint를 제공한다.
- 전체 포트폴리오 최적화 또는 실제 보유 현황 기반 리밸런싱 엔진은 아직 없다.

상태: Partial.

## 6단계: 매수 전략 수립

목표:

- 현재 보유 주식 상황과 목표 비중에 따라 리밸런싱 계획을 만든다.
- 얼마를 언제 어떤 순서로 매수/매도할지 전략화한다.

현재 구현:

- 독립된 매수 계획 엔진은 아직 없다.

상태: Planned.

## 7단계: 개별주식별 주요 이벤트/상황 기반 매수 전략 구체화

목표:

- 종목별 주요 이벤트와 체크아웃 지표를 정의한다.
- 이벤트 확인 방법을 세팅한다.
- 차트분석 기법을 이용해 진입 타점, 스탑로스, 저항선, 지지선, 피보나치 확장, 볼린저밴드, 차트 패턴, RSI 등을 전략에 반영한다.

현재 구현:

- stock price structure와 relative strength 일부만 있다.
- 종목별 이벤트 ledger와 chart strategy rulebook은 아직 없다.

상태: Planned.

## 8단계: 매수전략 실행

목표:

- 개별주 및 ETF 매매 전략을 관리하고 실행한다.
- 브로커 API 또는 주문 실행 계층을 연결한다.

현재 구현:

- 없음.

상태: Planned.

## 9단계: 결과 모니터링 및 전략 수정

목표:

- 증시 상황 변화에 따라 1단계부터 데이터를 업데이트하고 리밸런싱 판단을 수정한다.
- 투자 결과를 리뷰하고 개선점을 규칙화한다.
- 같은 실수를 반복하지 않도록 postmortem과 결과 아카이빙을 수행한다.

현재 구현:

- `/api/verification/{market}`와 일부 scorecard는 있다.
- 매매 결과 postmortem, 포트폴리오 성과 아카이브는 아직 없다.

상태: Planned.

## 우선순위

1. 현재 구현된 1~3단계의 신뢰성 점검.
2. 5단계 action/weight hint의 의미와 한계 명확화.
3. 4단계 이벤트 모듈 설계.
4. 6~9단계는 실제 자동매매 전 별도 검증 게이트 통과 후 진행.
