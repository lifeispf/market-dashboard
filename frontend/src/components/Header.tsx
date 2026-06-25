import type { Market } from "../api/client";

interface HeaderProps {
  market: Market;
  setMarket: (m: Market) => void;
  pill: string;
  asOf: string;
  // Snapshot build time (ISO+09:00), injected by the KV deploy generator. Optional:
  // absent in local dev where the backend serves routes directly. When present we
  // show "갱신 {YYYY-MM-DD HH:mm} KST" — the only timestamp that changes each refresh
  // (asOf is the last trading day, static intraday).
  generatedAt?: string;
}

// Format the snapshot build time in KST (Asia/Seoul) regardless of the viewer's
// timezone, so "갱신 시각" always reads as Korea wall-clock. formatToParts keeps the
// output deterministic ("YYYY-MM-DD HH:mm") instead of locale-specific punctuation.
function formatGeneratedAt(iso?: string): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(d);
  const get = (t: string) => parts.find((p) => p.type === t)?.value ?? "";
  const day = `${get("year")}-${get("month")}-${get("day")}`;
  const time = `${get("hour")}:${get("minute")}`;
  return `${day} ${time}`;
}

export default function Header({ market, setMarket, pill, asOf, generatedAt }: HeaderProps) {
  const gen = formatGeneratedAt(generatedAt);
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
      <span className="ld-asof">
        기준일 {asOf || "N/A"}
        {gen ? <> · 갱신 {gen} KST</> : " · 스냅샷"}
      </span>
    </div>
  );
}
