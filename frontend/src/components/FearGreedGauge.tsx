// NEW component — §13-1 Fear & Greed gauge. Not present in the prototype at all.
// Placed inside LiquiditySection, next to the existing REGIME gauge, but intentionally
// using a DIFFERENT color family (--fg-fear/--fg-neutral/--fg-greed, all blue/violet/
// magenta) instead of brass, so users don't read it as part of the REGIME composite.
// REGIME = "연료" (liquidity fuel/headroom). Fear&Greed = "심리" (market psychology) —
// a separate axis entirely; per the task this must never be merged into composite.
import { fearGreedColor } from "../lib/helpers";
import type { FearGreed } from "../api/types";

interface FearGreedGaugeProps {
  fearGreed: FearGreed;
}

export default function FearGreedGauge({ fearGreed }: FearGreedGaugeProps) {
  const { score, label, nAvailable, nTotal, factors } = fearGreed;
  const pct = score === null || score === undefined ? 0 : Math.max(0, Math.min(100, score));
  const colorBucket = fearGreedColor(score);

  return (
    <div className="ld-card ld-fg-card">
      <div className="ld-card-title">Fear &amp; Greed (심리)</div>
      <div className="ld-gaugebox">
        <div>
          <div className="ld-fg-val">
            {score === null || score === undefined ? "N/A" : Math.round(score)}
            {score !== null && score !== undefined && <span style={{ fontSize: 13, color: "var(--text-faint)" }}>/100</span>}
          </div>
          <div className="ld-gauge-lab">{label || "산정 불가"}</div>
          <div className="ld-avail">반영팩터 {nAvailable}/{nTotal}</div>
          <div className="track" style={{ marginTop: 10 }}>
            <div className={`fill fg-${colorBucket}`} style={{ width: pct + "%" }} />
          </div>
        </div>
        {factors && factors.length > 0 && (
          <div className="ld-fg-factors">
            {factors.map((f) => (
              <div className="ld-fg-factor" key={f.id}>
                <span className="fn">{f.name}</span>
                <div className="track">
                  {f.score !== null && f.score !== undefined ? (
                    <div className={`fill fg-${fearGreedColor(f.score)}`} style={{ width: Math.max(0, Math.min(100, f.score)) + "%" }} />
                  ) : null}
                </div>
                <span className="fv">{f.score === null || f.score === undefined ? "N/A" : Math.round(f.score)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
