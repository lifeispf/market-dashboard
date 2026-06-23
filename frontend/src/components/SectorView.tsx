// SectorView (§8.1 drilldown, Stage 6) — consumes the Sector tier Engine Core
// envelope from GET /api/sectors/{market} and renders per-sector Verdicts via
// the shared <VerdictCard> primitive. This is the first screen wired to the new
// tier endpoint (vs the frozen MarketPayload the rest of the dashboard uses);
// it surfaces the §21 relative-strength verdict layer the Sector Engine adds on
// top of the existing RRG metrics shown in LeadershipSection.
import { useEffect, useState } from "react";
import { fetchSectors, type Market, type Timeframe } from "../api/client";
import type { Concentration, EngineOutput } from "../api/types";
import VerdictCard from "../primitives/VerdictCard";
import { RISK_PROFILE_KR, RISK_PROFILE_ORDER, riskProfileColumn, sectorMomentumScore, type RiskProfile } from "../lib/helpers";

interface SectorViewProps {
  market: Market;
  tf: Timeframe;
  nameByCode: Record<string, string>;
}

// rs_momentum (extra, number|null) -> numeric tiebreak; null sorts as lowest.
function rsMomentumTiebreak(o: EngineOutput): number {
  const v = o.verdict.extra?.rs_momentum;
  return typeof v === "number" && !Number.isNaN(v) ? v : -Infinity;
}

// Group sectors by risk_profile column, then sort each column by signed momentum desc
// (strongest current up-mover on top, strongest down-mover on bottom), tiebreak rs_momentum desc.
function groupByRiskProfile(sectors: EngineOutput[]): Record<RiskProfile, EngineOutput[]> {
  const groups: Record<RiskProfile, EngineOutput[]> = { offensive: [], neutral: [], defensive: [] };
  for (const o of sectors) {
    groups[riskProfileColumn(o.verdict.extra)].push(o);
  }
  for (const key of RISK_PROFILE_ORDER) {
    groups[key].sort((a, b) => {
      const diff = sectorMomentumScore(b.verdict) - sectorMomentumScore(a.verdict);
      if (diff !== 0) return diff;
      return rsMomentumTiebreak(b) - rsMomentumTiebreak(a);
    });
  }
  return groups;
}

// Unsigned 0..100 percentage formatter for share-of-total metrics (cap weight,
// YTD contribution share) — distinct from helpers.fmtPct, which signs its output
// (+/-) for return-type metrics and would misleadingly prefix "+" here.
function fmtSharePct(n: number | null | undefined, digits = 1): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  return `${n.toFixed(digits)}%`;
}

// D-⑤ interpretation: high HHI + low effective_n + high top1 contribution ->
// narrow leadership ("쏠림 위험"). Thresholds are coarse, display-only heuristics
// (not a scoring/verdict signal) — purely to help the reader contextualize the numbers.
function concentrationInterpretation(c: Concentration): string | null {
  const { hhi, effective_n, top1_ytd_contribution_pct } = c;
  if (hhi === null && effective_n === null && top1_ytd_contribution_pct === null) return null;
  const narrow =
    (hhi !== null && hhi >= 0.25) ||
    (effective_n !== null && effective_n <= 4) ||
    (top1_ytd_contribution_pct !== null && top1_ytd_contribution_pct >= 50);
  return narrow
    ? "쏠림 위험 — 소수 섹터가 지수를 견인 중 (좁은 리더십)"
    : "분산 양호 — 다수 섹터가 균형있게 기여";
}

function ConcentrationPanel({ data }: { data: Concentration }) {
  const interpretation = concentrationInterpretation(data);
  return (
    <div className="sv-conc-panel">
      <div className="sv-conc-head">
        <span className="sv-conc-title">집중도 / 리더십 폭</span>
      </div>
      <div className="sv-conc-kpis">
        <div className="sv-conc-kpi">
          <span className="sv-conc-kpi-l">HHI</span>
          <span className="sv-conc-kpi-v">{data.hhi === null ? "N/A" : data.hhi.toFixed(3)}</span>
        </div>
        <div className="sv-conc-kpi">
          <span className="sv-conc-kpi-l">유효섹터수</span>
          <span className="sv-conc-kpi-v">{data.effective_n === null ? "N/A" : data.effective_n.toFixed(1)}</span>
        </div>
        <div className="sv-conc-kpi">
          <span className="sv-conc-kpi-l">상위1 시총비중</span>
          <span className="sv-conc-kpi-v">{fmtSharePct(data.top1_cap_pct)}</span>
        </div>
        <div className="sv-conc-kpi">
          <span className="sv-conc-kpi-l">상위1 YTD기여</span>
          <span className="sv-conc-kpi-v">{fmtSharePct(data.top1_ytd_contribution_pct)}</span>
        </div>
      </div>
      <div className="sv-conc-leaders">
        <span className="sv-conc-leaders-l">리더 섹터</span>
        <span className="sv-conc-leaders-v">{data.leaders.length > 0 ? data.leaders.join(", ") : "N/A"}</span>
      </div>
      {interpretation && <div className="sv-conc-note">{interpretation}</div>}
    </div>
  );
}

export default function SectorView({ market, tf, nameByCode }: SectorViewProps) {
  const [sectors, setSectors] = useState<EngineOutput[] | null>(null);
  const [concentration, setConcentration] = useState<Concentration | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setSectors(null);
    setConcentration(null);
    setError(null);
    fetchSectors(market, tf)
      .then((res) => {
        if (cancelled) return;
        setSectors(res.sectors);
        setConcentration(res.concentration ?? null);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [market, tf]);

  const columns = sectors ? groupByRiskProfile(sectors) : null;

  return (
    <div className="ld-section">
      <div className="ld-sec-head">
        <span className="ld-sec-num">SECTOR TIER</span>
        <h2 className="ld-h2">섹터 판정 (Sector Engine)</h2>
      </div>
      <p className="ld-sec-sub">
        섹터별 2축 판정 — 열(좌→우)은 위험선호 성격(공격/중립/방어, §고정 분류), 열 내부는 현재 방향·강도(모멘텀
        강한 순). §21 중심축(RRG 단일 윈도우 근사). 확신도는 검증 전이라 랭킹 신호로만.
      </p>

      {error && <div className="sv-msg" style={{ color: "var(--tight)" }}>⚠ 섹터 API 실패: {error}</div>}
      {!error && sectors === null && <div className="sv-msg">섹터 판정 불러오는 중…</div>}
      {!error && concentration && <ConcentrationPanel data={concentration} />}

      {columns && (
        <div className="sv-columns">
          {RISK_PROFILE_ORDER.map((key) => {
            const meta = RISK_PROFILE_KR[key];
            const items = columns[key];
            return (
              <div key={key} className={`sv-col sv-col-${key}`}>
                <div className="sv-col-head">
                  <span className={`sv-col-label sv-col-label-${key}`}>{meta.label}</span>
                  <span className="sv-col-subtitle">{meta.subtitle}</span>
                </div>
                {items.length === 0 ? (
                  <div className="sv-col-empty">해당 없음</div>
                ) : (
                  <div className="vc-grid sv-col-grid">
                    {items.map((o) => (
                      <VerdictCard key={o.entity_id} output={o} title={nameByCode[o.entity_id] ?? o.entity_id} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
