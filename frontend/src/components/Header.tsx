import type { Market } from "../api/client";

interface HeaderProps {
  market: Market;
  setMarket: (m: Market) => void;
  pill: string;
  asOf: string;
}

export default function Header({ market, setMarket, pill, asOf }: HeaderProps) {
  return (
    <div className="ld-header">
      <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        <div className="ld-toggle">
          {(["KOSPI", "NASDAQ"] as Market[]).map((m) => (
            <button key={m} className={market === m ? "active" : ""} onClick={() => setMarket(m)}>
              {m}
            </button>
          ))}
        </div>
        <span className="ld-pill">{pill}</span>
      </div>
      <span className="ld-asof">기준일 {asOf || "N/A"} · 스냅샷</span>
    </div>
  );
}
