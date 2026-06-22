// NEW component — §13-1 Fear & Greed gauge. Not present in the prototype at all.
// Placed inside LiquiditySection, next to the existing REGIME gauge, but intentionally
// using a DIFFERENT color family (--fg-fear/--fg-neutral/--fg-greed, all blue/violet/
// magenta) instead of brass, so users don't read it as part of the REGIME composite.
// REGIME = "연료" (liquidity fuel/headroom). Fear&Greed = "심리" (market psychology) —
// a separate axis entirely; per the task this must never be merged into composite.
//
// F&G is bipolar (0=extreme fear, 50=neutral, 100=extreme greed) — both extremes are
// signals (reversal risk), so a single fill-to-100 bar is semantically wrong. Replaced
// with a 5-zone diverging track (cut points 25/45/56/75, matching server LABEL_BANDS)
// and a needle marking the current score position.
import Sparkline from "./Sparkline";
import { fearGreedColor, fearGreedInterpretation } from "../lib/helpers";
import type { Timeframe } from "../api/client";
import type { FearGreed, ScorePoint } from "../api/types";

interface FearGreedGaugeProps {
  fearGreed: FearGreed;
  trend?: ScorePoint[];
  tf?: Timeframe;
}

// 5-zone diverging track cut points — mirrors server LABEL_BANDS (<25/<45/<56/<75/else).
const FG_ZONE_CUTS = [25, 45, 56, 75];

// tf -> native-cadence-aware label for the F&G score-trend sparkline.
const TF_TREND_LABEL: Record<Timeframe, string> = {
  "1D": "심리 추세 (일봉)",
  "1W": "심리 추세 (주봉)",
  "1M": "심리 추세 (월봉)",
  "1Q": "심리 추세 (분기봉)",
  "1Y": "심리 추세 (연봉)",
};

export default function FearGreedGauge({ fearGreed, trend = [], tf = "1D" }: FearGreedGaugeProps) {
  const { score, label, nAvailable, nTotal, factors } = fearGreed;
  const hasScore = score !== null && score !== undefined && !Number.isNaN(score);
  const pct = hasScore ? Math.max(0, Math.min(100, score as number)) : null;
  const colorBucket = fearGreedColor(score);
  const interp = fearGreedInterpretation(score);

  return (
    <div className="ld-card ld-fg-card">
      <div className="ld-card-title">Fear &amp; Greed (심리)</div>
      <div className="ld-gaugebox">
        <div>
          <div className="ld-fg-val">
            {hasScore ? Math.round(score as number) : "N/A"}
            {hasScore && <span style={{ fontSize: 13, color: "var(--text-faint)" }}>/100</span>}
          </div>
          <div className="ld-gauge-lab">{label || "산정 불가"}</div>
          <div className="ld-avail">반영팩터 {nAvailable}/{nTotal}</div>

          {/* bipolar diverging gauge: 5 zone bands + needle, centered at 50 */}
          <div className="ld-fg-bipolar" style={{ marginTop: 10 }}>
            <div className="ld-fg-zones">
              {FG_ZONE_CUTS.map((cut) => (
                <span className="ld-fg-zone-tick" key={cut} style={{ left: `${cut}%` }} />
              ))}
              <span className="ld-fg-zone-mid" style={{ left: "50%" }} />
              {pct !== null && (
                <span className={`ld-fg-needle fg-${colorBucket}`} style={{ left: `${pct}%` }} title={`score ${Math.round(score as number)}`} />
              )}
            </div>
            <div className="ld-fg-zone-labels">
              <span>공포</span>
              <span>중립</span>
              <span>탐욕</span>
            </div>
          </div>

          <div className="ld-fg-interp">{interp.text}</div>

          <div className="ld-fg-trend">
            <div className="ld-fg-trend-lab">{TF_TREND_LABEL[tf]}</div>
            {trend.length >= 2 ? (
              <Sparkline data={trend.map((p) => p.value)} showStats />
            ) : (
              <div className="ld-fg-trend-empty">데이터 부족</div>
            )}
          </div>
        </div>

        <details className="ld-fg-factors-details">
          <summary>구성 팩터 펼치기</summary>
          {factors && factors.length > 0 ? (
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
          ) : (
            <div className="ld-fg-factors-empty">팩터 데이터 없음</div>
          )}
        </details>

        <div className="ld-fg-note">
          ※ 자체 구축 4팩터 지수 (F1 모멘텀 · F2 강도 · F3 변동성 · F4 신용) — CNN의 7팩터 Fear&amp;Greed Index와는 별개입니다.
        </div>
      </div>
    </div>
  );
}
