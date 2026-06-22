# Open Questions — Opus 검토용 집계

> 본 문서는 `blueprint_micro/` 전체를 작성하며 발견한 보완 필요 사항·의문점을 한곳에 모은 것이다. 각 항목은 발생 위치(파일)를 명시했으니, 맥락이 필요하면 해당 파일의 🔶 표시 지점을 직접 확인할 것. 우선순위: 🔴 높음 / 🟡 중간 / ⚪ 낮음. **2026-06-21 사용자 결정 라운드 이후 ✅ = 해결/결정됨.**

## A. 구조적 공백 (원본 자체가 없음)

1. ✅ **해결(2026-06-21) §37 Stock Catalyst 결손** — Claude가 §26 Sector Catalyst 상속 구조 기반으로 실제 스펙 작성 완료(원본 PDF 아님, 파일 상단에 명시). → `stock_engine/37_catalyst.md`

2. ✅ **해결(2026-06-21) §39 Stock Rulebook 결손** — Claude가 §29 Sector Rulebook 형식을 3계층 구조에 맞게 변형해 작성 완료(원본 PDF 아님, 파일 상단에 명시). 가중치축/거부권축 분리, Sector→Stock 인터페이스, `position_size_hint` 출력, confidence 정책까지 포함. → `stock_engine/39_rulebook.md`

3. 🟡 **(미해결) Strategy Engine 전무** — 4단 구조(Macro→Sector→Stock→**Strategy**) 다이어그램에 이름만 등장하고 본문이 전혀 없다. 이번 결정 라운드의 범위 밖. §39의 신규 `position_size_hint` 필드가 잠정적으로 이 레이어 역할의 일부를 대신하고 있어, Strategy Engine을 실제로 설계할 때 역할 분담 재검토가 필요하다. → `stock_engine/38_risk.md`, `stock_engine/39_rulebook.md`, `00_index.md`

4. ⚪ **(미해결) Sector Engine §27·§28 번호 결번** — Catalyst(26)와 Rulebook(29) 사이 두 번호가 비어 있다. 의도적 예약인지 단순 결번인지 불명. 낮은 우선순위.

## B. 기존 매크로 엔진(기획안_v3/blueprint_v3)과의 정합성

5. ✅ **해결(2026-06-21) RRG·섹터 로테이션 중복** — 매크로 v2 "주도(RRG)"(`기획안.md` §5-2) + §13-3 "섹터 공·수 로테이션"(`기획안_expension_spec.md`)의 원시 계산을 단일 출처로 채택하고, 신규 §21/§24는 그 위에 다중 시간축·세부 분류만 추가하는 구조로 모듈화했다. 같은 공식을 두 곳에서 따로 구현하지 않는다. → `sector_engine/21_relative_strength.md`·`24_rotation.md`의 "Macro Engine과의 데이터 계약" 절, `sector_engine/00_overview.md`

6. ✅ **결정(2026-06-21) confidence 검증 게이트 — 유보** — 매크로 v3의 base-rate 보정 + 0.6 상한 + walk-forward 게이트(`기획안_v3.md` §A2·§H)를 신규 레이어에 **지금 강제하지 않기로 결정**했다. 충분한 트레이드/결과 데이터가 누적된 뒤 별도 단계로 추진. 그 전까지 모든 confidence·conviction은 "비검증 휴리스틱(랭킹 신호)"로 취급하고 실제 확률로 해석하지 않는다. → `stock_engine/39_rulebook.md` §8(정책 전문), `sector_engine/29_rulebook.md`

7. 🟡 **(미해결) Horizon(T0/T1/T2/T3) 명명 불일치** — Sector/Stock Engine의 T0(1~5일)/T1(1~6주)/T2(1~6개월)/T3(1~2년)와, 기존 매크로 §15의 T1(1~5일)/T2(1~4주) 정의가 같은 명칭(T1, T2)에 다른 기간을 가리킨다. 이번 라운드에서 다루지 않았다 — 같은 대시보드에서 호환되도록 한쪽을 리네이밍하거나 매핑표가 여전히 필요하다. → `sector_engine/00_overview.md`

8. ✅ **해결(2026-06-21) Macro→Sector 인터페이스 미정의** — 5번 해결과 함께 구체화됐다: 매크로 엔진은 `{sector_ticker, rs_ratio, rs_momentum, window}`(RRG)와 `cycle_role`/`rotation_spread`(로테이션)를 노출하고, Sector Engine이 이를 입력으로 받아 다중 시간축 해석을 추가하는 데이터 계약으로 정의했다. → `sector_engine/21_relative_strength.md`·`24_rotation.md`

## C. 데이터 소싱 현실성

9. ✅ **해결(2026-06-21) 유료/미국 특화 데이터 의존** — 13F·FINRA 공매도/Days-to-Cover·다크풀(OTC Transparency 근사)·내부자매매를 SEC EDGAR(키리스)·FINRA(키리스)로, 애널리스트 컨센서스/추정치를 Finnhub·FMP(무료키)로 재매핑했다. 진짜 유료 전용으로 남는 것은 실적콜 전체 트랜스크립트 1건뿐이며, 이마저 범위 축소(가이던스 정형 수치만 사용)로 제거했다. 집계 편의(WhaleWisdom급 정리)는 자체 구현이 필요하다는 트레이드오프는 남는다. → `data_sourcing.md`, `stock_engine/32_expectation.md`, `33_positioning.md`

10. ✅ **해결(2026-06-21) Catalyst 모듈의 NLP 파이프라인 요구** — 실적콜 전체 텍스트 NLP를 8-K 보도자료의 정형 가이던스 수치 사용으로 범위를 축소해, 별도 NLP 파이프라인 없이 처리하도록 재설계했다. 뉴스·SEC공시는 무료/무료키 소스로 충당. → `data_sourcing.md`, `sector_engine/26_catalyst.md`, `stock_engine/37_catalyst.md`

11. 🟡 **부분 해결(2026-06-21) 한국 시장 커버리지 공백** — DART(금융감독원 전자공시) Open API가 무료키로 제공된다는 점을 확인해 일부 포지셔닝 신호(5%대량보유·임원보유 변경)는 보완 가능하다. 다만 13F급 정기 전체 포지션 공시 제도가 한국에는 없어 완전한 대체는 아니다. Price Layer(§34~36)는 기존 KODEX/TIGER ETF 확장으로 커버되지만 Market Layer(§32~33)는 제한적 보완에 그친다. 기존 매크로 엔진의 "KOSPI breadth 인증벽 미해결"(`blueprint_v3.md` §5) 상태와 같은 계열의 잔존 격차다. → `data_sourcing.md`

## D. 모듈 내부 명세 공백 (전 모듈 공통)

12. 🟡 **(미해결) State 경계 정량 기준 부재** — "RS Leader"가 정확히 몇 %ile부터인지, "Quality Elite"가 ROIC/마진 몇 % 이상인지 등 State를 가르는 숫자 임계치가 여전히 없다(신규 작성된 §37/§39도 동일 — 일관성을 위해 의도적으로 정량 기준을 발명하지 않았다). 이는 기존 매크로 엔진의 원본 `기획안.md`(v2)가 거쳤던 것과 같은 단계이며, 그 다음에 `기획안_expension_spec`(§13/14/15) 같은 "정량화 패스"가 필요했다. Sector/Stock Engine도 같은 후속 작업이 필요하다.

13. 🟡 **부분 해결(2026-06-21) confidence/strength 산식 미정** — "검증 게이트를 지금 강제하지 않는다"는 **정책**은 결정됐다(B-6). 그러나 confidence/strength 값을 **어떻게 계산하는지(규칙기반 합치도? LLM 주관판단?)**의 **공식** 자체는 여전히 미정이다 — 정책 결정과 계산 공식 정의는 서로 다른 작업이다. 구현 단계에서 별도로 결정해야 한다.

## E. 사소한 점

14. ⚪ **(미해결, 무관) PDF 변환 아티팩트** — 원본 PDF 자체의 export 이슈로, 이번 blueprint 파일들에는 영향 없음. 원본을 같은 파이프라인으로 재출간할 일이 생기면 점검할 것.

15. ✅ **해결(2026-06-21) 우선순위 vs 거부권(Veto) 축 혼용** — Stock §30 우선순위 표가 "중요도"와 "거부권"을 한 표에 섞어 혼동을 유발했던 문제(Risk가 순위 7/8위지만 거부권은 최강)를, §39 Rulebook에서 "1. 가중치 축(Horizon별)"과 "2. 거부권 축"으로 분리해 해결했다. → `stock_engine/39_rulebook.md`, `stock_engine/00_overview.md`

## 요약 — 2026-06-21 결정 라운드 결과

지난 라운드에서 가장 시급하다고 표시했던 두 가지(§39 Stock Rulebook 작성 A-2, 매크로 엔진과의 RRG/로테이션 중복 해소 B-5)를 포함해 **8개 항목(1·2·5·6·8·9·10·15)이 해결**, **2개 항목(11·13)이 부분 해결**됐다. 전부 사용자의 명시적 결정(§37/§39 직접 설계 승인 · 매크로 모듈화 지시 · 검증게이트 유보 지시 · 무료키 허용 원칙)을 반영한 것이다.

**잔존 미결 사항(우선순위 순)**:
- 🟡 Strategy Engine 전무(A-3) — 가장 큰 잔존 공백. §39의 `position_size_hint`가 임시로 일부 역할을 대신하고 있어, 실제 설계 시 역할 재조정이 필요하다.
- 🟡 Horizon 명명 불일치(B-7) — 매크로 §15와 신규 레이어의 T1/T2가 다른 기간을 가리키는 문제, 아직 미결.
- 🟡 State 경계 정량 기준(D-12) · confidence/strength 산식(D-13) — 전 모듈 공통 "정량화 패스"가 구현 착수 직전에 필요.
- 🟡 한국 시장 커버리지(C-11) — DART로 일부 보완했으나 13F급 데이터는 여전히 미국 전용.
- ⚪ §27/§28 결번(A-4), PDF 변환 아티팩트(E-14) — 낮은 우선순위, 그대로 둠.
