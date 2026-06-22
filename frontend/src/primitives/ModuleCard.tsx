// Shared primitive (§8.2) — renders one ModuleOutput from the Engine Core
// envelope. Tier-agnostic: the same card shows a macro S0X axis, a sector
// relative-strength observation, or a stock module. An independent observation,
// never a conclusion (that's the Verdict).
import type { ModuleOutput } from "../api/types";
import { fmtNum, transitionKr } from "../lib/helpers";

interface ModuleCardProps {
  module: ModuleOutput;
}

// strength is 0..1 normalized → percent bar width.
function strengthPct(s: number | null): number {
  if (s === null || s === undefined) return 0;
  return Math.max(0, Math.min(1, s)) * 100;
}

export default function ModuleCard({ module }: ModuleCardProps) {
  // module_id like "sector.relative_strength" → short label "relative strength".
  const shortId = module.module_id.split(".").slice(1).join(".").replace(/_/g, " ");
  const degraded = module.state === null;

  return (
    <div className={`mc-card ${degraded ? "mc-degraded" : ""}`}>
      <div className="mc-head">
        <span className="mc-id">{shortId || module.module_id}</span>
        <span className="mc-state">{module.state ?? "관측 불가"}</span>
      </div>
      <div className="mc-meta">
        <span className="mc-trans">{transitionKr(module.transition)}</span>
        <span className="mc-strength-val">
          {module.strength === null ? "강도 N/A" : `강도 ${fmtNum(module.strength * 100, 0)}`}
        </span>
      </div>
      <div className="mc-bar">
        <div className="mc-bar-fill" style={{ width: `${strengthPct(module.strength)}%` }} />
      </div>
      <div className="mc-narr">{module.narrative}</div>
    </div>
  );
}
