// Adapted from prototype LeadershipSection — the biggest shape change in this port.
// Prototype: `sectors` was one object keyed by code, each entry inline-holding
// {name, weight, ytd, rsR, rsM, key:[Leader], star:[Leader]} OR {top: "A · B · C"} for
// sectors with no curated leaders.
// Contract: SPLIT into payload.sectors (flat array, financial fields only, no leaders)
// + payload.leaders (Record<code, {key, star}>, sparse — contract.md: "key/star 없는
// 섹터는 키 자체 생략 가능"). Treemap/RRG read from `sectors`; leader cards read from
// `leaders[selectedCode]`, defaulting to an empty-state when the code has no entry
// (confirmed live: NASDAQ only has leaders for 2 of its 11 sectors).
// `weight` (prototype) does not exist on the contract Sector -> treemap sizing uses
// `marketCap` instead (closest live analog of relative sector size).
// quadrant comes pre-computed from the server (no client-side quadrant() recompute,
// since rsRatio/rsMomentum here are centered on 100, not 1.0/0 like the prototype mock).
import { useEffect, useState } from "react";
import RRGChart from "./RRGChart";
import { AlertTriangle } from "./icons";
import { quadKr } from "../lib/helpers";
import { fetchSectors, fetchStocks, type Market, type Timeframe } from "../api/client";
import type {
  EngineOutput,
  HistoryResponse,
  RRGPoint,
  RrgConsensus,
  RrgWindowEntry,
  Sector,
  SectorLeaders,
  TrailPoint,
} from "../api/types";

// Phase E (now tf-scaled): the multi-window RRG horizon labels are no longer a fixed
// 1M/3M/6M/12M — the backend re-keys rrg_by_window per tf (see engine/sector/inputs.py
// RRG_WINDOWS_BY_TF). We derive the active labels at runtime from the fetched envelopes
// instead of hardcoding them, so this component tracks the backend without a redeploy.
// Static fallback (tf=1D's window set) used only while envelopes haven't resolved yet /
// none carry a usable rrg_by_window — keeps the grid/title non-empty during first paint.
const DEFAULT_RRG_WINDOWS = ["1M", "3M", "6M", "12M"];

// TF -> candle-cadence label, mirrors FlowSection.SPARK_LABEL wording (일봉/주봉/월봉/
// 분기봉/연봉) so the same tf reads identically across sections.
const TF_CANDLE_LABEL: Record<Timeframe, string> = {
  "1D": "일봉",
  "1W": "주봉",
  "1M": "월봉",
  "1Q": "분기봉",
  "1Y": "연봉",
};

// Ticker -> display name, joined from the curated `leaders` block (same pattern as
// StockView.buildNameByTicker — duplicated here rather than imported since StockView
// does not export it and we must not modify StockView.tsx).
function buildNameByTicker(leaders: Record<string, SectorLeaders>): Record<string, string> {
  const map: Record<string, string> = {};
  for (const code of Object.keys(leaders)) {
    const grp = leaders[code];
    for (const l of [...grp.key, ...(grp.star || [])]) map[l.ticker] = l.name;
  }
  return map;
}

interface LeadershipSectionProps {
  sectors: Sector[];
  leaders: Record<string, SectorLeaders>;
  market: Market;
  tf: Timeframe;
  history: HistoryResponse | null;
}

function treemapColor(ytd: number | null): string {
  if (ytd === null || ytd === undefined) return "rgba(127,147,196,.22)"; // locked-ish neutral for unknown
  if (ytd > 40) return "rgba(95,185,142,.45)";
  if (ytd > 15) return "rgba(95,185,142,.26)";
  if (ytd >= 0) return "rgba(205,177,90,.22)";
  return "rgba(208,107,74,.28)";
}

export default function LeadershipSection({ sectors, leaders, market, tf, history }: LeadershipSectionProps) {
  const defaultCode = sectors.length
    ? sectors.reduce((a, b) => ((b.marketCap ?? 0) > (a.marketCap ?? 0) ? b : a)).code
    : null;
  // App.tsx mounts this component with key={market}, so React fully remounts (and
  // re-runs these initializers) on every market toggle — no effect-based reset needed.
  const [selSector, setSelSector] = useState<string | null>(defaultCode);
  const [selLeader, setSelLeader] = useState<string | null>(null);

  // RRG trail overlay (Phase A, unchanged behavior) — `history` is now fetched once in
  // App.tsx (single /api/history fetch shared with LiquiditySection's Phase B score
  // trends) and passed down as a prop instead of this component self-fetching. Derive
  // the same {code: TrailPoint[]} map from it. Null/empty history degrades gracefully
  // to no trails (RRGChart already handles missing/empty trails without crashing).
  const [trails, setTrails] = useState<Record<string, TrailPoint[]>>({});
  useEffect(() => {
    if (!history) {
      setTrails({});
      return;
    }
    const next: Record<string, TrailPoint[]> = {};
    for (const s of history.sectors) {
      if (s.trail && s.trail.length) next[s.code] = s.trail;
    }
    setTrails(next);
  }, [history]);

  // Phase C: independent stock fetch for the sector-internal RRG ("who is strong/weak
  // WITHIN this sector", using sector_rs_ratio/momentum/quadrant added to verdict.extra).
  // StockView.tsx already fetches /api/stocks for its own card; this is a deliberate,
  // low-risk redundant GET rather than refactoring StockView to share state.
  const [stocks, setStocks] = useState<EngineOutput[] | null>(null);
  useEffect(() => {
    let cancelled = false;
    setStocks(null);
    fetchStocks(market, tf)
      .then((res) => {
        if (cancelled) return;
        setStocks(res.stocks);
      })
      .catch(() => {
        if (cancelled) return;
        setStocks([]); // null-safe degrade — empty list renders the "데이터 부족" placeholder
      });
    return () => {
      cancelled = true;
    };
  }, [market, tf]);

  // Phase E: independent /api/sectors fetch (Engine Core envelope) to read the
  // multi-window RRG fields stamped on verdict.extra (rrg_by_window/rrg_consensus).
  // The `sectors` prop above is the frozen single-window payload and does not carry
  // these — same low-risk redundant-GET pattern as the Phase C `stocks` fetch above.
  const [sectorEnvelopes, setSectorEnvelopes] = useState<EngineOutput[] | null>(null);
  useEffect(() => {
    let cancelled = false;
    setSectorEnvelopes(null);
    fetchSectors(market, tf)
      .then((res) => {
        if (cancelled) return;
        setSectorEnvelopes(res.sectors);
      })
      .catch(() => {
        if (cancelled) return;
        setSectorEnvelopes([]); // null-safe degrade — empty list renders empty windows
      });
    return () => {
      cancelled = true;
    };
  }, [market, tf]);

  // code -> rrg_by_window / code -> rrg_consensus, read from verdict.extra with safe
  // casts (extra is Record<string, unknown> per the Engine Core envelope contract).
  const rrgByWindowByCode: Record<string, Record<string, RrgWindowEntry | null> | undefined> = {};
  const rrgConsensusByCode: Record<string, RrgConsensus | null | undefined> = {};
  for (const o of sectorEnvelopes ?? []) {
    const extra = o.verdict?.extra;
    rrgByWindowByCode[o.entity_id] = extra?.rrg_by_window as Record<string, RrgWindowEntry | null> | undefined;
    rrgConsensusByCode[o.entity_id] = extra?.rrg_consensus as RrgConsensus | null | undefined;
  }

  const nameByTicker = buildNameByTicker(leaders);

  if (!sectors.length || !selSector) {
    return (
      <div className="ld-section">
        <div className="ld-sec-head">
          <span className="ld-sec-num">LAYER 3</span>
          <h2 className="ld-h2">주도 (섹터 · 종목)</h2>
        </div>
        <p className="ld-sec-sub">섹터 데이터 없음.</p>
      </div>
    );
  }

  const sel = sectors.find((s) => s.code === selSector) ?? sectors[0];
  const selLeaders: SectorLeaders | undefined = leaders[sel.code];
  const allLeaders = selLeaders
    ? [
        ...selLeaders.key.map((l) => ({ ...l, tag: "k" as const })),
        ...(selLeaders.star || []).map((l) => ({ ...l, tag: "s" as const })),
      ]
    : [];
  const selLeaderObj = allLeaders.find((l) => l.ticker === selLeader) || null;

  // Phase C: stocks belonging to the selected sector (matched via verdict.extra.sector_code,
  // which the backend now stamps on every stock output), mapped to RRGPoint using their
  // Sector-RS coordinates (sector_rs_ratio/momentum/quadrant — RS vs the sector itself, not
  // the index). Null-safe: stocks missing extra or with null sector_rs are excluded below.
  const sectorStockPoints: RRGPoint[] = (stocks ?? [])
    .filter((o) => o.verdict.extra?.sector_code === sel.code)
    .map((o) => ({
      code: o.entity_id,
      name: nameByTicker[o.entity_id] ?? o.entity_id,
      rsRatio: (o.verdict.extra?.sector_rs_ratio as number | null | undefined) ?? null,
      rsMomentum: (o.verdict.extra?.sector_rs_momentum as number | null | undefined) ?? null,
      quadrant: (o.verdict.extra?.sector_quadrant as RRGPoint["quadrant"] | null | undefined) ?? null,
    }));
  const plottableStockPoints = sectorStockPoints.filter((p) => p.rsRatio !== null && p.rsMomentum !== null);

  // Multi-window labels are now derived AT RUNTIME from the fetched data, not
  // hardcoded — the backend re-keys rrg_by_window per tf (e.g. tf=1W -> 3M/6M/12M/18M).
  // Take Object.keys() from the first sector envelope whose rrg_by_window is non-empty,
  // preserving the backend's own key order (already short->long server-side). Falls back
  // to DEFAULT_RRG_WINDOWS only while envelopes are still loading / all empty, so the
  // grid/title never render blank mid-fetch.
  let rrgWindows: string[] = DEFAULT_RRG_WINDOWS;
  for (const s of sectors) {
    const byWindow = rrgByWindowByCode[s.code];
    if (byWindow && Object.keys(byWindow).length) {
      rrgWindows = Object.keys(byWindow);
      break;
    }
  }

  // Build one RRGPoint[] per derived window from the sector envelopes' rrg_by_window
  // map. Sectors with a null entry for that window are skipped (RRGChart's own
  // plottable filter would drop them anyway, but we also need their name/code resolved
  // from the frozen `sectors` list since the envelope itself does not carry a display
  // name).
  const multiWindowPoints: Record<string, RRGPoint[]> = {};
  for (const w of rrgWindows) multiWindowPoints[w] = [];
  for (const s of sectors) {
    const byWindow = rrgByWindowByCode[s.code];
    if (!byWindow) continue;
    for (const w of rrgWindows) {
      const entry = byWindow[w];
      if (!entry) continue;
      multiWindowPoints[w].push({
        code: s.code,
        name: s.name,
        rsRatio: entry.ratio ?? null,
        rsMomentum: entry.momentum ?? null,
        quadrant: entry.quadrant ?? null,
      });
    }
  }

  const selConsensus = rrgConsensusByCode[sel.code];

  return (
    <div className="ld-section">
      <div className="ld-sec-head">
        <span className="ld-sec-num">LAYER 3</span>
        <h2 className="ld-h2">주도 (섹터 · 종목)</h2>
      </div>
      <p className="ld-sec-sub">연료가 지금 어느 섹터 · 종목으로 흐르는지 — 섹터 트리맵, 순환매(RRG), 주도주.</p>

      <div className="ld-card-title" style={{ marginTop: 6 }}>
        섹터 트리맵 (크기 = 시가총액, 색 = YTD)
      </div>
      <div className="ld-treemap">
        {sectors.map((s) => (
          <button
            key={s.code}
            className={`ld-cell ${selSector === s.code ? "sel" : ""}`}
            style={{ flexGrow: Math.max(1, Math.log10((s.marketCap ?? 1) + 1)), background: treemapColor(s.ytd) }}
            onClick={() => {
              setSelSector(s.code);
              setSelLeader(null);
            }}
          >
            <span className="nm">{s.name}</span>
            <span className="pc">{s.ytd === null ? "N/A" : `${s.ytd >= 0 ? "+" : ""}${s.ytd.toFixed(0)}%`}</span>
          </button>
        ))}
      </div>

      <div className="ld-grid2" style={{ marginTop: 18 }}>
        <div className="ld-card">
          <div className="ld-card-title">순환매 (RRG · {TF_CANDLE_LABEL[tf]}) — 상대강도 × 모멘텀</div>
          <RRGChart
            points={sectors}
            selectedKey={selSector}
            trails={trails}
            onSelect={(k) => {
              setSelSector(k);
              setSelLeader(null);
            }}
          />
          <div className="ld-rrg-legend">
            <span>
              <i style={{ background: "var(--open)" }} />
              leading · 주도 지속
            </span>
            <span>
              <i style={{ background: "var(--tight)" }} />
              weakening · 차익 임박
            </span>
            <span>
              <i style={{ background: "var(--neutral)" }} />
              improving · 순환매 진입
            </span>
            <span>
              <i style={{ background: "var(--locked)" }} />
              lagging · 소외
            </span>
          </div>
        </div>
        <div className="ld-card">
          <div className="ld-card-title">
            {sel.name} · {quadKr(sel.quadrant)}
          </div>
          <div className="ld-hint">섹터를 클릭하면 종목 정보가 바뀝니다. 카드를 클릭하면 상세가 펼쳐집니다.</div>
          {allLeaders.length > 0 ? (
            <>
              <div className="ld-cards">
                {allLeaders.map((l) => (
                  <button
                    key={l.ticker}
                    className={`ld-pcard ${selLeader === l.ticker ? "sel" : ""}`}
                    onClick={() => setSelLeader(selLeader === l.ticker ? null : l.ticker)}
                  >
                    <div className="top">
                      <span className="tk">{l.ticker}</span>
                      <span className={`ld-tag ${l.tag}`}>{l.tag === "k" ? "Key" : "Star"}</span>
                    </div>
                    <div className="nm">{l.name}</div>
                    <div className="rl">{l.role}</div>
                  </button>
                ))}
              </div>
              {selLeaderObj && (
                <div className="ld-detail">
                  <div className="dn">
                    {selLeaderObj.name}{" "}
                    <span style={{ fontFamily: "var(--mono)", fontSize: 12, color: "var(--text-faint)" }}>{selLeaderObj.ticker}</span>
                  </div>
                  <div className="dr">
                    {selLeaderObj.role} · {selLeaderObj.ytd === null ? "YTD N/A" : `${selLeaderObj.ytd >= 0 ? "+" : ""}${selLeaderObj.ytd.toFixed(1)}% YTD`}
                    {selLeaderObj.price !== null ? ` · ${selLeaderObj.price.toLocaleString()}` : ""}
                  </div>
                  <div className="thesis">{selLeaderObj.thesis}</div>
                  <div className="stats">
                    {selLeaderObj.stats.map(([k, v], i) => (
                      <div className="stat" key={i}>
                        <div className="sl">{k}</div>
                        <div className="sv">{v}</div>
                      </div>
                    ))}
                  </div>
                  <div className="ld-risk">
                    <AlertTriangle size={14} />
                    {selLeaderObj.risk}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="ld-simple">이 섹터는 큐레이션된 주도주 데이터가 없습니다 (leaders 미생략).</div>
          )}
        </div>
      </div>

      <div className="ld-card" style={{ marginTop: 18 }}>
        <div className="ld-card-title">멀티-윈도우 RRG ({rrgWindows.join(" · ")})</div>
        <div className="ld-hint">
          같은 섹터를 {rrgWindows.length}개 관측 호라이즌으로 동시에 본 결과 — 짧은 윈도우는 최근 추세 전환, 긴 윈도우는 구조적 위치를 반영합니다.
          호라이즌은 선택한 타임프레임({TF_CANDLE_LABEL[tf]})에 맞춰 자동으로 늘어나거나 줄어듭니다.
        </div>
        {sectorEnvelopes === null ? (
          <div className="ld-simple">멀티-윈도우 RRG 불러오는 중…</div>
        ) : (
          <div className="ld-mw-grid">
            {rrgWindows.map((w) => (
              <div className="ld-mw-cell" key={w}>
                <div className="ld-mw-cell-label">{w}</div>
                <RRGChart
                  points={multiWindowPoints[w]}
                  selectedKey={selSector}
                  onSelect={(k) => {
                    setSelSector(k);
                    setSelLeader(null);
                  }}
                  compact
                />
              </div>
            ))}
          </div>
        )}
        <div className="ld-mw-consensus">
          {selConsensus === null || selConsensus === undefined
            ? `${sel.name} 다중호라이즌 합의: 합의 산정 불가`
            : `${sel.name} 다중호라이즌 합의: ${quadKr(selConsensus.quadrant)} (일치도 ${
                selConsensus.agreement === null || selConsensus.agreement === undefined
                  ? "N/A"
                  : Math.round(selConsensus.agreement * 100)
              }%)`}
        </div>
      </div>

      <div className="ld-card" style={{ marginTop: 18 }}>
        <div className="ld-card-title">
          {sel.name} 내 종목 RRG (vs 섹터) · {TF_CANDLE_LABEL[tf]}
        </div>
        <div className="ld-hint">
          이 섹터 안에서 종목들의 상대강도 위치 — Sector-RS(섹터 자체 대비, 지수 대비가 아님) 기준. 같은 사분면 구조(LEADING/WEAKENING/IMPROVING/LAGGING)를 공유합니다.
        </div>
        {stocks === null ? (
          <div className="ld-simple">종목 데이터 불러오는 중…</div>
        ) : plottableStockPoints.length === 0 ? (
          <div className="ld-empty">데이터 부족 / 종목 RS 미가용</div>
        ) : (
          <>
            <RRGChart points={plottableStockPoints} />
            <div className="ld-rrg-legend">
              <span>
                <i style={{ background: "var(--open)" }} />
                leading · 섹터 내 주도
              </span>
              <span>
                <i style={{ background: "var(--tight)" }} />
                weakening · 차익 임박
              </span>
              <span>
                <i style={{ background: "var(--neutral)" }} />
                improving · 순환매 진입
              </span>
              <span>
                <i style={{ background: "var(--locked)" }} />
                lagging · 소외
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
