// Adapted from prototype LiquiditySection.
// Remaps: prototype `composite` -> payload.regime.composite; prototype `bands` ->
// payload.bands (often null live); prototype's client-side reconciliation() ->
// payload.reconciliation (server-provided). Layout changed from ld-grid2 (2 cols:
// ceiling | regime) to ld-grid3 (3 cols: ceiling | REGIME | Fear&Greed) to fit the new
// §13-1 gauge next to REGIME per the task spec, without touching REGIME's own styling.
import CeilingChart from "./CeilingChart";
import FearGreedGauge from "./FearGreedGauge";
import { DirIcon } from "./icons";
import { bandName, headroomColor, regimeLabel } from "../lib/helpers";
import type { Bands, FearGreed, Regime, Reconciliation, Source } from "../api/types";

interface LiquiditySectionProps {
  bands: Bands | null;
  level: number | null;
  regime: Regime;
  fearGreed: FearGreed;
  reconciliation: Reconciliation;
  sources: Source[];
}

// Regime composite band cut points (BASE | BULL | HYPER) — mirrors regimeLabel() in helpers.ts.
const REGIME_TICKS = [34, 67];
// Headroom-word cut points (tight | neutral | open) — mirrors headroomColor() in helpers.ts.
const HEADROOM_TICKS = [35, 60];

function BandTicks({ ticks }: { ticks: number[] }) {
  return (
    <div className="ld-track-ticks">
      {ticks.map((t) => (
        <span className="ld-track-tick" key={t} style={{ left: `${t}%` }} />
      ))}
    </div>
  );
}

export default function LiquiditySection({ bands, level, regime, fearGreed, reconciliation, sources }: LiquiditySectionProps) {
  const composite = regime.composite;
  const fillBucket = composite === null ? "locked" : composite >= 67 ? "tight" : composite >= 34 ? "neutral" : "open";

  return (
    <div className="ld-section">
      <div className="ld-sec-head">
        <span className="ld-sec-num">LAYER 2</span>
        <h2 className="ld-h2">여력 (유동성)</h2>
      </div>
      <p className="ld-sec-sub">그 움직임을 떠받칠 연료가 어디까지 차 있는지 — 시나리오별 천장과 6원천 헤드룸, 그리고 별도 축인 시장 심리(Fear&amp;Greed).</p>
      <div className="ld-grid3">
        <div className="ld-card">
          <div className="ld-card-title">시나리오별 천장 밴드</div>
          <CeilingChart bands={bands} current={level} supported={reconciliation.supportedCeiling} />
        </div>
        <div className="ld-card">
          <div className="ld-card-title">유동성 Regime (연료)</div>
          <div className="ld-gaugebox">
            <div>
              <div className="ld-gauge-val">
                {composite === null ? "N/A" : Math.round(composite)}
                {composite !== null && <span style={{ fontSize: 13, color: "var(--text-faint)" }}>/100</span>}
              </div>
              <div className="ld-gauge-lab">{regimeLabel(composite, regime.label)}</div>
              <div className="ld-avail">
                반영소스 {regime.nAvailable}/{regime.nTotal}
              </div>
              <div className="track" style={{ marginTop: 10, position: "relative" }}>
                <div className={`fill f-${fillBucket}`} style={{ width: (composite ?? 0) + "%" }} />
                <BandTicks ticks={REGIME_TICKS} />
              </div>
            </div>
            <div className="ld-reconcile">
              <span style={{ fontSize: 16 }}>{reconciliation.symbol}</span>
              <div className="t">
                {reconciliation.state === null ? (
                  <>
                    <b>정합성 산정 불가</b>
                    <br />
                    (bands/composite 데이터 부족)
                  </>
                ) : (
                  <>
                    <b>{reconciliation.priceBand ?? bandName(null)}</b> 상태 · {reconciliation.label}
                    <br />
                    유동성 지지 천장까지{" "}
                    <b>
                      {reconciliation.distancePct === null
                        ? "N/A"
                        : `${reconciliation.distancePct >= 0 ? "+" : ""}${reconciliation.distancePct.toFixed(0)}%`}
                    </b>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
        <FearGreedGauge fearGreed={fearGreed} />
      </div>
      <div className="ld-src-preview">
        {sources.map((s) => (
          <div className="ld-src-mini" key={s.id}>
            <span className="ld-src-mini-id">{s.id}</span>
            <div className="track ld-src-mini-track">
              <div className={`fill f-${headroomColor(s.headroom)}`} style={{ width: (s.headroom ?? 0) + "%" }} />
              <BandTicks ticks={HEADROOM_TICKS} />
            </div>
            <span className="ld-src-mini-score">{s.score === null ? "N/A" : Math.round(s.score)}</span>
            <span className={`ld-src-mini-dir c-${headroomColor(s.headroom)}`}>
              <DirIcon dir={s.dir} size={10} />
            </span>
          </div>
        ))}
      </div>
      <details className="ld-src-details">
        <summary>6개 원천 상세 펼치기</summary>
        <div className="ld-sources">
          {sources.map((s) => (
            <div className="ld-src" key={s.id}>
              <div className="ld-src-top">
                <span className="ld-src-id">{s.id}</span>
                <span className="ld-src-name">{s.name}</span>
                <span className="ld-src-scope">{s.scope}</span>
              </div>
              <div className="ld-src-state">{s.state}</div>
              <div className="ld-src-gauge-row">
                <span style={{ fontFamily: "var(--mono)", fontSize: 10.5, color: "var(--text-faint)" }}>헤드룸</span>
                <span className="gv">{s.headroom === null ? "N/A" : `${s.headroom}/100`}</span>
              </div>
              <div className="track" style={{ position: "relative" }}>
                <div className={`fill f-${headroomColor(s.headroom)}`} style={{ width: (s.headroom ?? 0) + "%" }} />
                <BandTicks ticks={HEADROOM_TICKS} />
              </div>
              <div className={`ld-dir c-${headroomColor(s.headroom)}`}>
                <DirIcon dir={s.dir} size={11} />
                {s.dirLabel}
              </div>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
