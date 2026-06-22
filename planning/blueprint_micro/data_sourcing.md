# 데이터 소싱 매핑 — 무료/무료키/유료 분류

> `90_open_questions.md` C-9·C-10 해결, C-11 부분 해결. 사용자 결정(2026-06-21): "기존 키리스/무료 원칙을 최대한 존중하되, **무료라면 키 발급은 허용**." 기존 매크로 엔진의 원칙(`blueprint_v3.md` §5: "무료 키는 FRED 하나, 나머지 키리스")을 Sector/Stock Engine까지 확장 적용하되, 무료 가입형 API 키는 허용 범위로 넓힌다.

## 분류 기준

- ✅ **키리스 무료** — 키 발급 없이 바로 호출 가능
- 🔑 **무료키 발급** — 가입·키 발급 필요하지만 비용 없음(호출량 제한 있을 수 있음)
- 🚫 **유료 전용** — 무료 등가물 없음, 결정 필요(구매 vs 범위 축소 vs 포기)

## §32 Expectation

| 데이터 | 분류 | 소스 제안 |
|---|---|---|
| 애널리스트 컨센서스(EPS·매출 추정치) | 🔑무료키 | Finnhub 무료티어(`/stock/recommendation`, `/stock/estimate`) 또는 FMP 무료티어(`analyst-estimates`) — 둘 다 호출량 제한 |
| 추정치 수정(Revision) 추이 | 🔑무료키(제한적) | 위와 동일 소스의 베스트에포트. 깊은 히스토리가 부족하면 매주 스냅샷을 자체 적재해 수정추이를 직접 축적 |
| 가이던스(Raise/Maintain/Cut) | ✅키리스무료 | SEC EDGAR Full-Text Search API(8-K Item 2.02/7.01 exhibit) — 키 불필요, 파싱은 직접 구현 |
| Estimate Dispersion(분산) | 🔑무료키(제한적) | Finnhub/FMP 무료티어 — 유료 벤더(I/B/E/S 등) 대비 정확도 낮을 수 있음, 1차 근사로 시작 |
| 옵션 기반 시장 내재 기대(IV/Skew) | ✅키리스무료 | CBOE 옵션체인 — 기존 매크로 엔진이 이미 `derivatives.options.chains`(cboe, 키리스)로 사용 중인 **동일 소스 재사용**(`blueprint_v3.md` §3) |

## §33 Positioning

| 데이터 | 분류 | 소스 제안 |
|---|---|---|
| 13F 기관보유 | ✅키리스무료 | SEC EDGAR 구조화 13F 데이터(13F-HR XML) — 키 불필요. 단, 분기지연(최대 45일) + WhaleWisdom류 집계 편의 없음(직접 파싱·집계 구현 필요) |
| FINRA 공매도(Short Interest) | ✅키리스무료 | FINRA 격주 공매도 공시 파일 — 기존 매크로 v3가 Triage 피처용으로 이미 검토한 **동일 소스**(`기획안_v3.md` §3). 포지셔닝 모듈과 매크로 Triage가 같은 파이프라인을 공유하도록 통합 권장(중복 호출 방지) |
| 다크풀/OTC 거래량 | ✅키리스무료(근사) | FINRA OTC Transparency(ATS) 데이터 — 주간/월간 집계. 실시간 다크풀 프린트(유료, Unusual Whales 등)의 완전한 대체는 아니지만, 무료로 얻을 수 있는 가장 근접한 근사치 |
| 내부자 매매(Form 4) | ✅키리스무료 | SEC EDGAR Form 4 — 키 불필요. OpenInsider.com 같은 집계 사이트는 스크레이핑(ToS 확인 필요, 권장하지 않음 — EDGAR 직접 파싱이 안전) |
| 옵션 포지셔닝(Put/Call) | ✅키리스무료 | CBOE 옵션체인 재사용(§32와 동일 소스) |
| 애널리스트 Rating 분포 | 🔑무료키 | Finnhub/FMP 무료티어 |

## §26 Sector Catalyst / §37 Stock Catalyst

| 데이터 | 분류 | 소스 제안 |
|---|---|---|
| 뉴스 헤드라인 | 🔑무료키(제한적) | Finnhub 뉴스 무료티어, NewsAPI 무료티어(100req/day), 또는 기업 IR RSS(키 불필요지만 커버리지 낮음) |
| SEC 공시(8-K 등) | ✅키리스무료 | SEC EDGAR Full-Text Search API |
| 실적콜 텍스트(전체 트랜스크립트) | 🚫유료전용 → **범위 축소로 해결** | 대량 수집은 사실상 유료(AlphaSense/Sentieo 등). **권장: 전체 트랜스크립트 NLP 대신 8-K 실적보도자료의 정형 수치(가이던스 숫자)만 사용** — §32 Expectation의 Guidance 항목과 동일한 키리스 소스로 충당 가능, 별도 NLP 파이프라인 불필요 |
| FDA/제품 승인 캘린더 | 스크레이핑(무료, 키 옵션 없음) | biopharmcatalyst.com 등 — ToS 확인 필요, 해당 업종(바이오)에만 적용 |
| 원자재/정책 데이터 | ✅키리스무료 | FRED(기존 매크로 엔진과 동일 키 재사용), 정부 정책 캘린더는 기존 매크로 v3의 `economy.calendar`(OpenBB, 키리스) 재사용 |

## 정책 요약

위 표를 따르면 진짜 "유료 전용"으로 남는 항목은 **실적콜 전체 텍스트** 1건뿐이며, 이마저 범위를 축소(가이던스 정형 수치만 사용)하면 제거된다. 13F·공매도·다크풀·내부자매매는 전부 SEC/FINRA 1차 데이터로 무료(키리스) 충당 가능하나, **집계 편의(WhaleWisdom급 정리)는 자체 구현해야 한다**는 트레이드오프가 있다 — 이는 데이터 비용이 아니라 개발 비용으로 이전된 것이며, 구현 우선순위 산정 시 반영 필요.

## 한국 시장 커버리지 (C-11, 부분 해결)

위 소스 대부분(13F/FINRA/SEC EDGAR/Finnhub 미국 추정치)은 미국 시장 전용이며 한국 직접 대응물이 없다는 한계는 해소되지 않는다. 다만 한 가지 보완 발견: **금융감독원 DART(전자공시시스템)가 무료 Open API를 제공**(키 발급 필요하지만 무료) — 5% 이상 대량보유·임원 보유 변경 공시 등 일부 포지셔닝 신호의 한국 근사치로 쓸 수 있으나, 13F처럼 기관 전체 포지션을 정기적으로 공시하는 제도는 아니라 완전한 대체는 아니다. Sector Engine §21이 이미 KODEX/TIGER ETF로 가격 데이터는 커버하므로(`sector_engine/21_relative_strength.md`), Stock Engine의 한국 종목 확장은 **Price Layer(§34~36)는 가능, Market Layer(§32~33)는 DART로 제한적 보완, 완전한 기관/숏 포지셔닝 데이터는 미해결**로 정리한다.

## 기존 매크로 엔진과의 공유 원칙

신규로 추가되는 키(Finnhub/FMP 등)는 기존 "FRED 1개 키" 원칙과 같은 수준으로 — `config.json`에 명시적으로 등록하고, 호출량 제한을 캐싱(`st.cache_data`)으로 관리한다. 같은 데이터(예: FINRA 공매도)를 매크로 Triage와 Sector/Stock Positioning이 각각 따로 fetch하지 않도록, 데이터 레이어는 엔진 간 공유 가능한 단일 fetcher로 설계할 것.
