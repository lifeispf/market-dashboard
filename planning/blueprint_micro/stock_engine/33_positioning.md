# Positioning (§33)

> 원본: `micro Ideation/33_positioning.pdf` | Market Layer

## 핵심 질문

누가 이미 들고 있는가? 시장은 한쪽으로 과도하게 치우쳐 있는가? 추가 매수 여력이 있는가?

## 설계 철학

"좋은 뉴스보다 **누가 아직 안 샀는가**가 더 중요할 수 있다" — 주가는 새로운 매수자가 움직이므로, Positioning은 현재보다 미래 수급의 여지를 설명한다.

## 5개 하위축

Institutional Ownership(기관보유%, Top홀더 집중도, ETF포함여부) · Crowding(Buy비율/컨센서스강도/목표가프리미엄/포지션 집중도) · Short Positioning(숏비율/Days to Cover/Put-Call Ratio) · Sentiment(뉴스/애널리스트/리테일) · Ownership Trend(13F 변화/기관Flow/내부자매수)

## Composite State (★ = 매력도)

Under-owned★★★★★ > Healthy★★★★ > Crowded★★★ > Overcrowded★★ > Forced Selling★

## Archetypes

Under-owned Compounder(Quality↑Positioning↓=최고의 기회) · Consensus Darling(Expectation↑Crowding↑=과열위험) · Short Squeeze(RS↑Short Interest↑=폭발적 상승 가능성) · Overcrowded Winner(RS↑Positioning↑=후반부) · Forced Liquidation(Participation↓Positioning↓=위험)

## 데이터

Institutional/ETF/Insider Ownership, **Short Interest**, Option Positioning, Analyst Ratings, **Hedge Fund 13F**, Sentiment Indicators

## Veto Rules

Forced Selling → Long 금지 / Extreme Crowding → Conviction 제한 / Ownership Trend 악화 → 포지션 축소

## Limitations

Crowded Trade가 반드시 나쁜 투자는 아니다 — 강한 구조적 리더는 오래 혼잡 상태를 유지할 수 있다(§33-19).

## Output Schema

```json
{"state":"Under-owned","transition":"Improving","strength":4,"confidence":0.81,
 "narrative":"기관 보유 비중이 낮고 추가 자금 유입 여력이 존재한다.",
 "risks":["기관 매수 부재","Catalyst 부족"]}
```

## ✅ 데이터 소싱 — 해결(한국 시장은 부분 해결)

13F·FINRA 공매도·다크풀(OTC Transparency 근사)·내부자매매(Form 4)는 전부 SEC/FINRA 1차 데이터로 **키리스 무료** 충당 가능하다(`../data_sourcing.md` "§33 Positioning" 참조, `../90_open_questions.md` C-9 해결). 다만 13F는 여전히 분기 지연(최대 45일)이라는 데이터 자체의 한계는 남는다. FINRA 공매도/다크풀 데이터는 기존 매크로 v3가 "Triage 피처"용으로 검토한 데이터(`기획안_v3.md` §3)와 **동일 소스**이므로, 두 엔진이 따로 fetch하지 않도록 데이터 레이어를 공유 설계할 것(`../data_sourcing.md` "기존 매크로 엔진과의 공유 원칙"). 한국 시장은 DART Open API로 일부 보완 가능하나 13F급 정기 전체 포지션 공시는 없어 완전한 대체는 아니다(`../90_open_questions.md` C-11, 부분 해결).
