// StockView (§8.1 drilldown, Stage 6 — Stock tier) — consumes GET
// /api/stocks/{market} (Engine Core envelope) and renders per-stock Verdicts via
// the shared <VerdictCard>. Surfaces the Price-layer verdict (§35 RS × §34
// structure) + position_size_hint the Stock Engine adds on top of the curated
// leaders shown in LeadershipSection. Stock names join from the frozen payload's
// `leaders` block (code→{key,star}→ticker→name) — no backend change.
import { useEffect, useState } from "react";
import { fetchStocks, type Market, type Timeframe } from "../api/client";
import type { EngineOutput, MarketPayload } from "../api/types";
import VerdictCard from "../primitives/VerdictCard";

interface StockViewProps {
  market: Market;
  tf: Timeframe;
  leaders: MarketPayload["leaders"];
}

function buildNameByTicker(leaders: MarketPayload["leaders"]): Record<string, string> {
  const map: Record<string, string> = {};
  for (const code of Object.keys(leaders)) {
    const grp = leaders[code];
    for (const l of [...grp.key, ...(grp.star || [])]) map[l.ticker] = l.name;
  }
  return map;
}

export default function StockView({ market, tf, leaders }: StockViewProps) {
  const [stocks, setStocks] = useState<EngineOutput[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const nameByTicker = buildNameByTicker(leaders);

  useEffect(() => {
    let cancelled = false;
    setStocks(null);
    setError(null);
    fetchStocks(market, tf)
      .then((res) => {
        if (cancelled) return;
        // Rank by verdict strength desc — strongest setups first.
        const sorted = [...res.stocks].sort((a, b) => b.verdict.strength - a.verdict.strength);
        setStocks(sorted);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [market, tf]);

  return (
    <div className="ld-section">
      <div className="ld-sec-head">
        <span className="ld-sec-num">STOCK TIER</span>
        <h2 className="ld-h2">종목 판정 (Stock Engine)</h2>
      </div>
      <p className="ld-sec-sub">
        주도주 Price-레이어 판정 — §35 Market RS × §34 가격 구조. 강도순 정렬, 포지션 사이즈 힌트(§39). 확신도는 검증 전이라 랭킹 신호로만.
      </p>

      {error && <div className="sv-msg" style={{ color: "var(--tight)" }}>⚠ 종목 API 실패: {error}</div>}
      {!error && stocks === null && <div className="sv-msg">종목 판정 불러오는 중…</div>}
      {stocks && stocks.length === 0 && <div className="sv-msg">큐레이션된 주도주가 없습니다.</div>}

      {stocks && stocks.length > 0 && (
        <div className="vc-grid">
          {stocks.map((o) => (
            <VerdictCard key={o.entity_id} output={o} title={nameByTicker[o.entity_id] ?? o.entity_id} />
          ))}
        </div>
      )}
    </div>
  );
}
