// Adapted from prototype FreshnessBar. Prototype FRESHNESS mock had {label, freq, last,
// stale}; contract FreshnessItem adds `source` and allows `last: null` (live: many
// FRED/KRX-dependent rows have last=null since keys aren't configured). Render null
// `last` as "N/A" rather than an empty/undefined string.
//
// D-⑥ SLA emphasis: visually call out `stale: true` rows (warning badge, distinct
// border/background) and surface a one-line summary (stale count + oldest known
// `last` date among stale rows) so a reader doesn't have to scan every chip.
import type { FreshnessItem } from "../api/types";

interface FreshnessBarProps {
  freshness: FreshnessItem[];
}

// Oldest `last` (lexicographic ISO-date compare; null treated as "unknown", not oldest)
// among stale rows — null-safe, never throws on missing/malformed dates.
function oldestStaleDate(freshness: FreshnessItem[]): string | null {
  let oldest: string | null = null;
  for (const f of freshness) {
    if (!f.stale || !f.last) continue;
    if (oldest === null || f.last < oldest) oldest = f.last;
  }
  return oldest;
}

export default function FreshnessBar({ freshness }: FreshnessBarProps) {
  const staleCount = freshness.filter((f) => f.stale).length;
  const oldest = oldestStaleDate(freshness);

  return (
    <div className="ld-section" style={{ paddingTop: 22 }}>
      <div className="ld-sec-head">
        <span className="ld-sec-num">H</span>
        <h2 className="ld-h2" style={{ fontSize: 15 }}>
          데이터 신선도
        </h2>
      </div>
      {staleCount > 0 && (
        <div className="ld-fresh-sla">
          <span className="ld-fresh-sla-badge">⚠ 갱신 지연</span>
          {staleCount}개 소스 갱신 지연{oldest ? ` · 최장 지연 ${oldest}` : ""}
        </div>
      )}
      <div className="ld-fresh">
        {freshness.map((f, i) => (
          <span className={`ld-fresh-item ${f.stale ? "ld-fresh-item-stale" : ""}`} key={i}>
            <span className={`ld-fresh-dot ${f.stale ? "bad" : "ok"}`} />
            {f.label} ({f.source}) · {f.last ?? "N/A"} · {f.freq}
            {f.stale && <span className="ld-fresh-stale-badge">지연</span>}
          </span>
        ))}
      </div>
    </div>
  );
}
