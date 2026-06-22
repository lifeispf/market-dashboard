# Sector Rotation (§24)

> 원본: `micro Ideation/24_sector_rotation.pdf`

## 핵심 질문

자금은 공격형/방어형 중 어디로 이동하며, 현재는 Early/Mid/Late Cycle 중 어디인가?

## 설계 철학

자금은 Technology→Industrials→Financials→Energy→Defensives 순으로 순환한다는 전통적 경기순환 가정에 기반한다. **섹터의 강약보다 섹터 간 자금 이동(=Rotation)이 더 중요할 수 있다.**

## 섹터 분류

- Growth(Technology/반도체/소프트웨어) · Cyclical(산업재/금융/소재/에너지) · Defensive(헬스케어/필수소비재/유틸리티/통신) · Consumer(임의소비재/필수소비재)
- Risk-On: Technology/반도체/임의소비재/산업재/금융 ↔ Risk-Off: 유틸리티/필수소비재/헬스케어/통신

## 지표

Offensive/Defensive Ratio = (Technology+반도체+XLY) / (Staples+Utilities+Healthcare), Growth/Value Ratio, Cyclical/Defensive Ratio, Equal Weight Leadership, RRG Rotation, Momentum Spread(공격형 vs 방어형)

## 산출 구조

- **State**: Strong Risk-On / Risk-On / Neutral / Risk-Off / Defensive Leadership
- **Transition**: Accelerating / Stable / Decelerating / Reversing
- **Cycle 해석**: Early(Technology/반도체/임의소비재 주도) → Mid(산업재/금융 확산) → Late(에너지/소재 주도) → Defensive(유틸리티/필수소비재/헬스케어 주도)

## 핵심 충돌 패턴

| 패턴 | 의미 |
|---|---|
| RS↑ + Rotation↑ | Healthy Bull |
| RS↑ + Rotation↓ | 후반부 |
| Breadth↑ + Rotation↑ | Strong Expansion |
| Participation↑ + Rotation↓ | 기관의 방어적 자금 이동 |
| 지수↑ + 방어주↑ | Late Cycle 경고 |

## 한계 — 중요

AI 사이클과 같은 **구조적 변화**가 발생하면 전통적 경기순환 모델은 일시적으로 작동하지 않을 수 있다(§24-15에서 명시적으로 인정). Macro Regime/RS/Breadth/Participation과 함께 해석 필수.

## Output Schema

```json
{"state":"Risk-On","transition":"Accelerating","strength":4,"confidence":0.84,
 "narrative":"자금이 공격형 섹터로 이동하고 있으며 위험 선호가 강화되고 있다.",
 "risks":["방어주 상대강도 상승","Rotation 둔화"]}
```

## ✅ Macro Engine과의 데이터 계약 — 중복 해소 (결정 2026-06-21)

`90_open_questions.md` B-5 해결. 공격/방어 분류와 스프레드 계산의 원천은 기존 매크로 §13-3(`기획안_expension_spec.md`)의 `sectors.json.cycle_role`(offensive/defensive/neutral) 필드와 `rotation_spread` 계산을 **그대로 재사용**한다. Sector Engine §24는 Growth/Cyclical/Defensive/Consumer라는 자체 분류 체계를 독립적으로 새로 만들지 않고, 기존 `cycle_role` 태그 **위에 얹는 보조 세분류**로 둔다.

| 계층 | 담당 | 산출 |
|---|---|---|
| 매크로 엔진(기존, 변경 없음) | `cycle_role` 태그(수동 큐레이션) + `offensive_basket`/`defensive_basket`/`rotation_spread`(20일 모멘텀 기반 단일 지표, config `momentum_window`) | 크로스 내러티브 배지용 "공격 우위·위험선호 확대" 한 줄 |
| Sector Engine §24(본 모듈, 신규) | 동일 `cycle_role` 태그 기반 + 섹터-페어 단위 로테이션 흐름(어느 섹터→어느 섹터, 속도) + Early/Mid/Late/Defensive **Cycle 단계** 판정 + State(Strong Risk-On~Defensive Leadership)/Transition(Accelerating~Reversing) | 로테이션 정밀 진단 |

`cycle_role`은 LLM 일반지식 기반의 미검증 분류라는 한계(`기획안_expension_spec.md` §13-3 "검증 안 됨, 팀 합의 필요")를 Sector Engine §24도 그대로 승계하며, 매크로 엔진과 동일하게 **분기 단위 재검토**가 필요하다. neutral 태그 섹터는 매크로 엔진과 동일하게 스프레드 계산에서 제외한다(트리맵·RRG 표시에는 포함).

## 🔶 Opus 검토 (잔존)

위 데이터 계약이 실제 구현(코드 레벨 함수 공유)으로 이어지는지는 구현 단계에서 별도 확인 필요 — 본 문서는 설계 결정만 명문화한 것이다.
