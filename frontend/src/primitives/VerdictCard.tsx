// Shared primitive (§8.2) — renders one Verdict from the Engine Core envelope.
// Tier-agnostic: macro regime, sector lead pattern, or stock verdict all render
// here. Shows direction/strength/lead_pattern/conviction(+verified gate)/
// narrative/risks. The `verified` flag (§9.1) is load-bearing: until walk-forward
// backtesting lands, conviction is an unverified heuristic and is labeled as such.
import type { ActionLevels, EngineOutput } from "../api/types";
import { directionColor, DIRECTION_KR, DIRECTION_ARROW, sizeHint } from "../lib/helpers";
import ModuleCard from "./ModuleCard";

interface VerdictCardProps {
  output: EngineOutput;
  title: string; // human label for entity_id (e.g. sector name)
}

export default function VerdictCard({ output, title }: VerdictCardProps) {
  const v = output.verdict;
  const color = directionColor(v.direction);
  // strength 0..4 → 4 pips.
  const pips = [0, 1, 2, 3].map((i) => i < v.strength);
  const size = sizeHint(v.extra?.position_size_hint); // present on stock tier (§39)

  return (
    <div className="vc-card">
      <div className="vc-head">
        <div className="vc-title-wrap">
          <span className="vc-title">{title}</span>
          <span className="vc-entity">{output.entity_id}</span>
        </div>
        <span className={`vc-dir vc-${color}`}>
          {DIRECTION_ARROW[v.direction]} {DIRECTION_KR[v.direction]}
        </span>
      </div>

      <div className="vc-row">
        {v.lead_pattern && <span className={`vc-pattern vc-${color}`}>{v.lead_pattern}</span>}
        <span className="vc-pips">
          {pips.map((on, i) => (
            <i key={i} className={`vc-pip ${on ? `vc-pip-${color}` : ""}`} />
          ))}
        </span>
        {size && <span className={`vc-size vc-${size.color}`}>사이즈 {size.label}</span>}
        {output.mode === "degraded" && <span className="vc-degraded-tag">데이터 일부 결손</span>}
      </div>

      {v.narrative && <div className="vc-narr">{v.narrative}</div>}

      <div className="vc-conviction">
        {v.verified ? (
          <span>확신도 {v.conviction === null ? "N/A" : (v.conviction * 100).toFixed(0)}</span>
        ) : (
          <span className="vc-unverified" title="walk-forward 검증 전 — 랭킹 신호로만 사용 (§9.1)">
            비검증 휴리스틱 · 랭킹 신호
          </span>
        )}
      </div>

      {v.risks.length > 0 && (
        <ul className="vc-risks">
          {v.risks.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}

      {/* DI-3 실행 레벨(투명 룰) — 항상 disclaimer 동반. 투자자문 아님. */}
      {(() => {
        const a = v.extra?.action as ActionLevels | null | undefined;
        if (!a) return null;
        return (
          <div className="vc-action">
            <div className="vc-action-h">실행 · 기계적 룰</div>
            <div className="vc-action-row">
              <span className="k">진입</span>
              <span className="val">{a.entry}</span>
            </div>
            {a.stop !== null && (
              <div className="vc-action-row">
                <span className="k">손절</span>
                <span className="val">
                  {a.stop.toLocaleString()} <em>({a.stop_pct}%)</em> · {a.stop_rule}
                </span>
              </div>
            )}
            <div className="vc-action-row">
              <span className="k">비중</span>
              <span className="val">
                {a.weight_pct}% <em>· {a.weight_rule}</em>
              </span>
            </div>
            <div className="vc-action-disc">⚠ {a.disclaimer}</div>
          </div>
        );
      })()}

      {output.modules.length > 0 && (
        <div className="vc-modules">
          {output.modules.map((m) => (
            <ModuleCard key={m.module_id} module={m} />
          ))}
        </div>
      )}
    </div>
  );
}
