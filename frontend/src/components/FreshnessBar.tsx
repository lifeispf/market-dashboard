// Adapted from prototype FreshnessBar. Prototype FRESHNESS mock had {label, freq, last,
// stale}; contract FreshnessItem adds `source` and allows `last: null` (live: many
// FRED/KRX-dependent rows have last=null since keys aren't configured). Render null
// `last` as "N/A" rather than an empty/undefined string.
import type { FreshnessItem } from "../api/types";

interface FreshnessBarProps {
  freshness: FreshnessItem[];
}

export default function FreshnessBar({ freshness }: FreshnessBarProps) {
  return (
    <div className="ld-section" style={{ paddingTop: 22 }}>
      <div className="ld-sec-head">
        <span className="ld-sec-num">H</span>
        <h2 className="ld-h2" style={{ fontSize: 15 }}>
          데이터 신선도
        </h2>
      </div>
      <div className="ld-fresh">
        {freshness.map((f, i) => (
          <span className="ld-fresh-item" key={i}>
            <span className={`ld-fresh-dot ${f.stale ? "bad" : "ok"}`} />
            {f.label} ({f.source}) · {f.last ?? "N/A"} · {f.freq}
          </span>
        ))}
      </div>
    </div>
  );
}
