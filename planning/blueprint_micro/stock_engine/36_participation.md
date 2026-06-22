# Participation (§36)

> 원본: `micro Ideation/36_Participation.pdf` | Price Layer | **T0~T1에서 가장 강력한 확인(confirm) 모듈**

## 핵심 질문

실제로 돈이 들어오고 있는가? RS가 보여주는 방향에 수급이 동반되는가?

## 설계 철학

가격=결과, 거래량=확신. RS(방향) × Participation(강도)이 Price Layer의 핵심 듀얼 축이다(Sector Engine의 RS×Momentum과 평행한 구조).

## 4개 하위축

Volume(RVOL/평균거래량/Breakout Volume, State: Explosive~Weak) · Money Flow(OBV/CMF/MFI/VWAP, State: Strong Inflow~Negative) · Accumulation(Up/Down Volume, A/D, State: Strong Accumulation~Distribution) · Ownership(기관보유/내부자매수/ETF포함/Fund Flow)

## Composite State

Strong Accumulation★★★★★ > Accumulation★★★★ > Neutral★★★ > Distribution★★ > Capitulation★

## Archetypes

Institutional Leader(RS↑Participation↑=최고의 리더) · Quiet Accumulation(RS보통+Participation↑=잠재적 리더) · Distribution Phase(RS↓Participation↓=약세) · Exhaustion(가격↑Participation↓=후반부) · False Breakout(RS↑Participation↓=위험)

## Veto Rules

Participation=Breaking → Breakout 무효 / Distribution+Weakening → Long Conviction 제한 / Capitulation → Risk 급증

## Output Schema

```json
{"state":"Accumulation","transition":"Improving","strength":4,"confidence":0.86,
 "narrative":"거래량 증가와 자금 유입이 상승 추세를 지지하고 있다.",
 "risks":["RVOL 둔화","기관 자금 이탈"]}
```

## 🔶 Opus 검토

Sector Engine §23(Sector Participation)과 거의 동일한 지표셋(RVOL/OBV/CMF)을 종목 단위로 재계산한다 — 계산 대상(섹터ETF vs 개별종목)이 달라 중복은 아니지만, 두 모듈의 State/Transition 정의·임계치가 일관되게 맞춰져 있는지(같은 "Strong Accumulation"이 섹터와 종목에서 같은 기준을 쓰는지) 확인이 필요하다.
