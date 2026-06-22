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
import { useState } from "react";
import RRGChart from "./RRGChart";
import { AlertTriangle } from "./icons";
import { quadKr } from "../lib/helpers";
import type { Sector, SectorLeaders } from "../api/types";

interface LeadershipSectionProps {
  sectors: Sector[];
  leaders: Record<string, SectorLeaders>;
}

function treemapColor(ytd: number | null): string {
  if (ytd === null || ytd === undefined) return "rgba(127,147,196,.22)"; // locked-ish neutral for unknown
  if (ytd > 40) return "rgba(95,185,142,.45)";
  if (ytd > 15) return "rgba(95,185,142,.26)";
  if (ytd >= 0) return "rgba(205,177,90,.22)";
  return "rgba(208,107,74,.28)";
}

export default function LeadershipSection({ sectors, leaders }: LeadershipSectionProps) {
  const defaultCode = sectors.length
    ? sectors.reduce((a, b) => ((b.marketCap ?? 0) > (a.marketCap ?? 0) ? b : a)).code
    : null;
  // App.tsx mounts this component with key={market}, so React fully remounts (and
  // re-runs these initializers) on every market toggle — no effect-based reset needed.
  const [selSector, setSelSector] = useState<string | null>(defaultCode);
  const [selLeader, setSelLeader] = useState<string | null>(null);

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
          <div className="ld-card-title">순환매 (RRG) — 상대강도 × 모멘텀</div>
          <RRGChart
            sectors={sectors}
            selectedKey={selSector}
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
    </div>
  );
}
