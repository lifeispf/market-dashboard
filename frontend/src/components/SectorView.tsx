// SectorView (§8.1 drilldown, Stage 6) — consumes the Sector tier Engine Core
// envelope from GET /api/sectors/{market} and renders per-sector Verdicts via
// the shared <VerdictCard> primitive. This is the first screen wired to the new
// tier endpoint (vs the frozen MarketPayload the rest of the dashboard uses);
// it surfaces the §21 relative-strength verdict layer the Sector Engine adds on
// top of the existing RRG metrics shown in LeadershipSection.
import { useEffect, useState } from "react";
import { fetchSectors, type Market, type Timeframe } from "../api/client";
import type { EngineOutput } from "../api/types";
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

export default function SectorView({ market, tf, nameByCode }: SectorViewProps) {
  const [sectors, setSectors] = useState<EngineOutput[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setSectors(null);
    setError(null);
    fetchSectors(market, tf)
      .then((res) => {
        if (cancelled) return;
        setSectors(res.sectors);
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
