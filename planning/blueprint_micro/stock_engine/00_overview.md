# Stock Intelligence Engine — 개요 (§30)

> 원본: `micro Ideation/30_stock_engine.md.pdf`
> 위치: Macro Engine → Sector Engine → **Stock Engine** → Strategy Engine

## 정의

"어떤 종목을 선택해야 하는가?" — 개별 기업의 강점·기대·수급·가격구조·촉매·위험을 통합 해석해 확률적 우위가 있는 종목을 식별한다.

## 설계 철학

개별 종목은 하나의 숫자로 평가될 수 없다. **기업(Fundamental) × 시장(Expectation) × 가격(Technical)** 세 축의 상호작용을 해석하는 시스템이다.

## 3계층 구조

| 계층 | 모듈 |
|---|---|
| Fundamental Layer (기업 자체) | Quality(§31) · Catalyst(§37) · Risk(§38) |
| Market Layer (시장의 기대) | Expectation(§32) · Positioning(§33) |
| Price Layer (가격 행동) | Price Structure(§34) · Relative Strength(§35) · Participation(§36) |

## 모듈 8개 + Rulebook

§31 Quality(좋은 회사?) · §32 Expectation(시장 기대?) · §33 Positioning(누가 들고 있나?) · §34 Price Structure(언제 살 것인가?) · §35 Relative Strength(시장이 뭘 사나?) · §36 Participation(돈이 들어오나?) · §37 Catalyst(왜 움직이나?) · §38 Risk(뭐가 틀릴 수 있나?) → **§39 Stock Rulebook**에서 종합

> ✅ **결정(2026-06-21)**: §37(Catalyst)과 §39(Rulebook)는 원본 PDF 16개 중에 존재하지 않았으나(`90_open_questions.md` A-1·A-2), 형제 모듈 패턴과 §26/§29의 구조를 토대로 Claude가 새로 설계해 채웠다. 두 파일 모두 상단에 "Claude 작성" 표시가 있어 원본 소싱 모듈과 구분된다 — Opus 검토 시 이 구분을 유지할 것. 상세는 `37_catalyst.md`, `39_rulebook.md` 참조.

## Time Horizons (T0~T3)

T0(1~5거래일, 단타) / T1(1~6주, 스윙) / T2(1~6개월, 포지션) / T3(1~2년, 장기투자)

모듈별 중요도가 시간축에 따라 달라진다 — 예: Quality는 T3에서 최강 Veto, Price Structure/Participation/RS는 T0~T1에서 최강, Risk는 **모든 시간축에서 매우 중요**(유일하게 전 구간 최고 등급).

## 모듈 우선순위 (기본값)

1.RS → 2.Expectation → 3.Quality → 4.Participation → 5.Catalyst → 6.Price Structure → 7.Risk → 8.Positioning

> ✅ **해결**: 이 "우선순위(중요도 가중치)" 리스트에서 Risk는 7위지만, §38 본문은 "Risk가 가장 강력한 Veto 권한을 가지며 모든 모듈 위에서 작동한다"고 명시해 순위(중요도)와 거부권(override 권한)이라는 서로 다른 두 축이 한 표에 섞여 있었다(`../90_open_questions.md` E-15). `39_rulebook.md`에서 "1. 가중치 축(Horizon별)"과 "2. 거부권 축"을 별도 표로 분리해 해결했다.

## 신뢰도(confidence) 정책

각 모듈 Output Schema의 `confidence`·Rulebook의 `conviction`은 **비검증 휴리스틱**이다. 정책 전문은 `39_rulebook.md` §8 참조.

## Veto / Conflict 원칙

- 장기투자: Quality 붕괴 → 기타 신호 무효
- 단기전략: Participation 붕괴 → Breakout 무효
- Event Risk → 포지션 크기 제한
- 불일치가 가장 중요한 정보: `Quality↑Expectation↓→Value Trap` / `RS↑Participation↓→False Breakout` / `Catalyst↑Positioning(Under-owned)→Early Leader` / `Price↑Risk↑→취약한 상승`

## Output 구조

각 모듈은 `{state, transition, strength, confidence, narrative}`만 출력하고 **최종 결론은 내리지 않는다** — Sector Engine과 동일하게 종합은 Rulebook(§39, 결손)의 역할이다.

## Sector Engine과의 관계

"좋은 종목이라도 좋은 섹터에 속하지 않으면 성과가 제한될 수 있다" → Sector Engine이 Stock Engine의 **상위 필터** 역할을 수행한다.

## 다음 읽을 문서

- 모듈별 상세: `31_quality.md` ~ `38_risk.md`
- 결손 모듈 안내: `37_catalyst.md`, `39_rulebook.md`
- 상위 레이어: `../sector_engine/00_overview.md`
- 전체 이슈 집계: `../90_open_questions.md`
