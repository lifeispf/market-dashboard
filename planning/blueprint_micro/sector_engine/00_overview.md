# Sector Intelligence Engine — 개요 (§20)

> 원본: `micro Ideation/20_sector_engine.md.pdf`
> 위치: Macro Engine → **Sector Engine** → Stock Engine → Strategy Engine

## 정의

Macro Engine이 "시장 전체가 위험 선호 환경인가?"에 답한다면, Sector Engine은 "어느 영역으로 자금이 이동하고 있는가?"에 답하는 중간 레이어다.

## 목적

- 주도 섹터 탐색
- 순환매 탐지
- 섹터 내부 건강도 평가
- 위험 선호 변화 감지

## 설계 철학

- 모듈 점수를 합산하지 않는다 — 각 모듈은 독립 관측기(observer)이며, 충돌·정렬의 해석은 Rulebook(§29)이 전담한다.
- 목적은 예측이 아니라 확률적 우위(probabilistic edge) 탐색이다.

→ 기존 매크로 엔진의 "6축 합산 금지·불일치=신호" 철학(`blueprint_v3.md` §4)과 동일한 원칙이 섹터 레벨로 재적용된 것.

## 모듈 구조 (6개 독립 모듈 + 1개 해석 레이어)

| § | 모듈 | 핵심 질문 |
|---|---|---|
| 21 | Relative Strength | 어느 섹터가 시장보다 강한가? |
| 22 | Breadth | 상승이 건강하게 확산되는가? |
| 23 | Participation | 실제 자금 유입이 있는가? |
| 24 | Rotation | 공격형↔방어형, 자금은 어디로? |
| 25 | Momentum | 추세가 강화되는가? |
| 26 | Catalyst | 왜 움직이는가? |
| 29 | **Rulebook** | 위 6축을 해석해 Direction/Strength/Conviction/Narrative/Invalidation 생성 |

모든 관측 모듈은 공통 구조를 따른다: `Question → Indicators → State → Transition → Conflict`. 산출은 점수가 아니라 **State**(Leading/Improving/Weakening/Lagging류)이며, Transition(Improving/Stable/Weakening/Breaking)이 현재 State보다 중요하다는 원칙이 모든 모듈에서 반복된다.

## Horizons

T0: 1~5 거래일 / T1: 1~6주 / T2: 1~6개월

## 신뢰도(confidence) 정책

각 모듈 Output Schema의 `confidence`는 **비검증 휴리스틱**이다 — 검증 게이트 적용 여부는 결정했으나(아래), 게이트 자체는 아직 가동 전이다. 정책 전문은 `29_rulebook.md` "신뢰도 정책" 절 참조.

## 기존 매크로 엔진과의 관계 / 중복 해소

> ✅ **결정(2026-06-21)**: §21 RRG·§24 공격/방어 로테이션은 기존 macro 프로젝트의 v2 "주도(RRG)" 모듈(`기획안.md` §5-2) 및 §13-3 "섹터 공·수 로테이션"(`기획안_expension_spec.md`)과 **계산을 공유하고 해석만 분리**하는 방식으로 모듈화한다 — 매크로 엔진은 단일 윈도우 스냅샷(크로스 내러티브 배지용), Sector Engine은 동일 원시값을 다중 시간축·세부 분류로 재해석. 두 곳에서 같은 공식을 따로 구현하지 않는다. 상세 데이터 계약은 `21_relative_strength.md`·`24_rotation.md`의 "Macro Engine과의 데이터 계약" 절 참조. (`90_open_questions.md` B-5, B-8 해결)

> 🔶 **[Opus 검토]** Horizon 명명(T0/T1/T2)이 기존 매크로 §15의 T1/T2 정의(T1=1~5일, T2=1~4주)와 폭이 다르다. 두 체계를 같은 대시보드에서 같이 쓸 경우 "T1"이라는 단어가 문서마다 다른 기간을 가리키게 되어 혼란 소지가 있다.

## 다음 읽을 문서

- 모듈별 상세: `21_relative_strength.md` ~ `26_catalyst.md`
- 최종 해석 로직: `29_rulebook.md`
- 상위 레이어: `../stock_engine/00_overview.md`
- 전체 이슈 집계: `../90_open_questions.md`
