import { useEffect, useState } from "react";
import { fetchMarket, type Market } from "./api/client";
import type { MarketPayload } from "./api/types";
import "./design/styles.css";

import GlobalMacroBar from "./components/GlobalMacroBar";
import Header from "./components/Header";
import CrossNarrativeBadge from "./components/CrossNarrativeBadge";
import FlowSection from "./components/FlowSection";
import LiquiditySection from "./components/LiquiditySection";
import LeadershipSection from "./components/LeadershipSection";
import SectorView from "./components/SectorView";
import StockView from "./components/StockView";
import WatchlistTable from "./components/WatchlistTable";
import FreshnessBar from "./components/FreshnessBar";
import Footer from "./components/Footer";

// Real dashboard, replacing the Track 0 seam-check screen. Ports
// planning/market-dashboard-prototype.jsx's design + component structure, but every
// component now consumes the live MarketPayload contract (frontend/src/api/types.ts)
// via fetchMarket() instead of the prototype's hardcoded MARKETS mock.
function App() {
  const [market, setMarket] = useState<Market>("KOSPI");
  const [data, setData] = useState<MarketPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchMarket(market)
      .then((payload) => {
        if (cancelled) return;
        setData(payload);
        setError(null);
      })
      .catch((e) => {
        if (cancelled) return;
        setData(null);
        setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [market]);

  // Guard against a stale payload from the previous market flashing while the new
  // market's fetch is in flight (the cancelled-aware effect above clears `error` but
  // intentionally leaves the old `data` in place momentarily; this gate prevents it
  // from rendering under the new market's header).
  const payload = data?.market === market ? data : null;

  if (error) {
    return (
      <div className="ld-root">
        <div className="ld-error">⚠ API 호출 실패: {error}</div>
      </div>
    );
  }

  if (!payload) {
    return (
      <div className="ld-root">
        <div className="ld-loading">불러오는 중…</div>
      </div>
    );
  }

  return (
    <div className="ld-root">
      <div className="ld-proto-banner">
        <b>유동성 천장 대시보드</b> · {payload.market} · {payload.asOf} 기준 · {payload._mode === "live" ? "라이브 API" : "mock"} (_mode:{" "}
        {payload._mode})
      </div>
      <GlobalMacroBar sources={payload.sources} />
      <div className="ld-wrap">
        <Header market={market} setMarket={setMarket} pill={payload.pill} asOf={payload.asOf} />
        <CrossNarrativeBadge narrative={payload.narrative} rec={payload.reconciliation} />
        <FlowSection flow={payload.flow} />
        <LiquiditySection
          bands={payload.bands}
          level={payload.flow.level}
          regime={payload.regime}
          fearGreed={payload.fearGreed}
          reconciliation={payload.reconciliation}
          sources={payload.sources}
        />
        <LeadershipSection key={market} sectors={payload.sectors} leaders={payload.leaders} />
        <SectorView
          key={`sv-${market}`}
          market={market}
          nameByCode={Object.fromEntries(payload.sectors.map((s) => [s.code, s.name]))}
        />
        <StockView key={`stk-${market}`} market={market} leaders={payload.leaders} />
        <WatchlistTable watchlist={payload.watchlist} />
        <FreshnessBar freshness={payload.freshness} />
        <Footer mode={payload._mode} source={payload.source} />
      </div>
    </div>
  );
}

export default App;
