// SectorView (§8.1 drilldown, Stage 6) — consumes the Sector tier Engine Core
// envelope from GET /api/sectors/{market} and renders per-sector Verdicts via
// the shared <VerdictCard> primitive. This is the first screen wired to the new
// tier endpoint (vs the frozen MarketPayload the rest of the dashboard uses);
// it surfaces the §21 relative-strength verdict layer the Sector Engine adds on
// top of the existing RRG metrics shown in LeadershipSection.
import { useEffect, useState } from "react";
import { fetchSectors, type Market } from "../api/client";
import type { EngineOutput } from "../api/types";
import VerdictCard from "../primitives/VerdictCard";

interface SectorViewProps {
  market: Market;
  nameByCode: Record<string, string>;
}

const STRENGTH_ORDER = (o: EngineOutput) => o.verdict.strength;

export default function SectorView({ market, nameByCode }: SectorViewProps) {
  const [sectors, setSectors] = useState<EngineOutput[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setSectors(null);
    setError(null);
    fetchSectors(market)
      .then((res) => {
        if (cancelled) return;
        // Rank by verdict strength desc — leaders first (the drilldown's point).
        const sorted = [...res.sectors].sort((a, b) => STRENGTH_ORDER(b) - STRENGTH_ORDER(a));
        setSectors(sorted);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [market]);

  return (
    <div className="ld-section">
      <div className="ld-sec-head">
        <span className="ld-sec-num">SECTOR TIER</span>
        <h2 className="ld-h2">섹터 판정 (Sector Engine)</h2>
      </div>
      <p className="ld-sec-sub">
        섹터별 상대강도 판정 — §21 중심축(RRG 단일 윈도우 근사). 강도순 정렬. 확신도는 검증 전이라 랭킹 신호로만.
      </p>

      {error && <div className="sv-msg" style={{ color: "var(--tight)" }}>⚠ 섹터 API 실패: {error}</div>}
      {!error && sectors === null && <div className="sv-msg">섹터 판정 불러오는 중…</div>}

      {sectors && (
        <div className="vc-grid">
          {sectors.map((o) => (
            <VerdictCard key={o.entity_id} output={o} title={nameByCode[o.entity_id] ?? o.entity_id} />
          ))}
        </div>
      )}
    </div>
  );
}
