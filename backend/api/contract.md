# API 계약 (FROZEN — Track 0)

이 문서는 백엔드(Track A)와 프론트(Track B)가 **독립 병렬 작업**하기 위한 seam이다.
**이 스키마는 동결됐다.** 변경이 필요하면 리드가 이 문서 + `frontend/src/api/types.ts`를
함께 갱신하고 양 트랙에 통지한다. 서브에이전트가 임의로 바꾸지 않는다.

## 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/market/{market}` | `market` ∈ `KOSPI`\|`NASDAQ`. 전체 대시보드 페이로드. 404 on unknown. |
| GET | `/api/health` | `{status, db, fredKey, krxAuth}` — 키/인증 가용성 |
| GET | `/` | 서비스 메타 |

## `/api/market/{market}` 응답 스키마

최상위 키(순서 무관, 전부 필수): `market, asOf, source, pill, flow, bands, regime,
fearGreed, reconciliation, sources, sectors, leaders, narrative, watchlist, freshness, _mode`.

- **flow**: `{level, chgPct, yoyPct, fwdPER, trailingPER, breadthText, breadthNote, volLabel, volValue, volDir, spark[]}`
  - 미가용 수치는 `null` (프론트는 null → "N/A" 렌더). `volDir` ∈ `up|down|flat`.
- **bands**: `{base:{lo,hi}, bull:{lo,hi}, hyper:{lo,hi}, hyperOpen:bool}`. EPS 미입력 시 `bands: null`.
- **regime**: `{composite:0-100|null, label, nAvailable, nTotal}`.
- **fearGreed**: `{score:0-100|null, label, nAvailable, nTotal, factors:[{id,name,value,score}]}`.
  - 🆕 §13-1. REGIME과 별개 축. KOSPI는 breadth 인증벽 시 nAvailable 줄어듦(예: 3/6).
- **reconciliation**: `{state:"aligned"|"overheated"|"slack"|null, symbol, label, supportedCeiling, priceBand, distancePct}`.
- **sources**: 길이 6 배열. 각 `{id:"S01".."S06", name, scope, headroom:0-100|null, dir, dirLabel, state, score:0-100|null}`.
- **sectors**: 배열. 각 `{code, name, marketCap:number|null, ytd:number|null, rsRatio:number|null, rsMomentum:number|null, quadrant:"leading"|"weakening"|"improving"|"lagging"|null}`.
- **leaders**: `{ [sectorCode]: {key:[Leader], star:[Leader]} }`. key/star 없는 섹터는 키 자체 생략 가능.
  - Leader: `{ticker, name, role, price:number|null, ytd:number|null, thesis, stats:[[label,value]], risk, asOf}`.
- **narrative**: `{flow, liquidity, leadership, reconciliation}` — 전부 string, 라이브 자동생성.
- **watchlist**: 배열. 각 `{label, trigger, meaning, status:"fired"|"quiet"|"manual_check"|"unknown"}`.
- **freshness**: 배열. 각 `{label, source, freq, last:"YYYY-MM-DD"|null, stale:bool}`.
- **_mode**: `"mock"`(Track 0) | `"live"`(Track A 완료 후). 디버그/검증용.

## 불변식

- 데이터 미가용은 **항상 `null`**, 절대 크래시·임의값 금지(기존 graceful-degradation 계승).
- 숫자 단위: `marketCap`은 원/달러 절대값, `level`/`bands`는 지수 포인트, `ytd`/`chgPct`/`distancePct`는 퍼센트(예: 38 = +38%).
- `_mode`로 mock/live를 구분 — 프론트는 둘 다 동일 렌더.
