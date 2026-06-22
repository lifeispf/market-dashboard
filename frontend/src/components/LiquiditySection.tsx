// Adapted from prototype LiquiditySection.
// Remaps: prototype `composite` -> payload.regime.composite; prototype `bands` ->
// payload.bands (often null live); prototype's client-side reconciliation() ->
// payload.reconciliation (server-provided). Layout changed from ld-grid2 (2 cols:
// ceiling | regime) to ld-grid3 (3 cols: ceiling | REGIME | Fear&Greed) to fit the new
// §13-1 gauge next to REGIME per the task spec, without touching REGIME's own styling.
import CeilingChart from "./CeilingChart";
import FearGreedGauge from "./FearGreedGauge";
import Sparkline from "./Sparkline";
import { DirIcon } from "./icons";
import { bandName, headroomColor, regimeLabel } from "../lib/helpers";
import type { Timeframe } from "../api/client";
import type { Bands, FearGreed, HistoryResponse, Regime, Reconciliation, Source } from "../api/types";

interface LiquiditySectionProps {
  bands: Bands | null;
  level: number | null;
  regime: Regime;
  fearGreed: FearGreed;
  reconciliation: Reconciliation;
  sources: Source[];
  history: HistoryResponse | null;
  tf: Timeframe;
}

// tf -> native-cadence-aware label wording for the composite score-trend sparkline.
const TF_TREND_LABEL: Record<Timeframe, string> = {
  "1D": "유동성 점수 추세 (일봉)",
  "1W": "유동성 점수 추세 (주봉)",
  "1M": "유동성 점수 추세 (월봉)",
  "1Q": "유동성 점수 추세 (분기봉)",
  "1Y": "유동성 점수 추세 (연봉)",
};

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

export default function LiquiditySection({ bands, level, regime, fearGreed, reconciliation, sources, history, tf }: LiquiditySectionProps) {
  const composite = regime.composite;
  const fillBucket = composite === null ? "locked" : composite >= 67 ? "tight" : composite >= 34 ? "neutral" : "open";

  // Phase B — composite score-trend sparkline (B-class snapshot indicator: headline
  // composite stays "current value", this is the *trend over the tf window* layered
  // underneath). history.scores.composite is oldest->newest [{date,value}]; map to the
  // plain number[] Sparkline expects. <2 points (sparse scores_daily accrual, or
  // history fetch failed) -> "데이터 부족" fallback, never crash.
  const compositeTrend = history?.scores?.composite ?? [];
  const compositeTrendValues = compositeTrend.map((p) => p.value);

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
              <div className="ld-score-trend">
                <div className="ld-score-trend-lab">{TF_TREND_LABEL[tf]}</div>
                {compositeTrendValues.length >= 2 ? (
                  <Sparkline data={compositeTrendValues} showStats />
                ) : (
                  <div className="ld-score-trend-empty">데이터 부족(누적 중)</div>
                )}
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

            <details className="ld-regime-factors-details">
              <summary>구성 팩터 펼치기</summary>
              {sources.length > 0 ? (
                <div className="ld-regime-factors">
                  {sources.map((s) => {
                    // s.id is "S01".."S06" (uppercase); scores_daily columns are lowercase.
                    const scoreKey = s.id.toLowerCase();
                    const srcTrendValues = (history?.scores?.[scoreKey] ?? []).map((p) => p.value);
                    return (
                      <div className="ld-regime-factor" key={s.id}>
                        <div className="ld-regime-factor-row">
                          <span className="fid">{s.id}</span>
                          <span className="fn">
                            {s.name}
                            {s.id === "S01" && <span className="ld-src-native">네이티브: 주간</span>}
                          </span>
                          <div className="track" style={{ position: "relative" }}>
                            <div className={`fill f-${headroomColor(s.headroom)}`} style={{ width: (s.headroom ?? 0) + "%" }} />
                            <BandTicks ticks={HEADROOM_TICKS} />
                          </div>
                          <span className="fv">{s.headroom === null ? "N/A" : Math.round(s.headroom)}</span>
                          <span className={`ld-regime-factor-dir c-${headroomColor(s.headroom)}`}>
                            <DirIcon dir={s.dir} size={10} />
                            {s.dirLabel}
                          </span>
                        </div>
                        {srcTrendValues.length >= 2 ? (
                          <div className="ld-src-trend">
                            <Sparkline data={srcTrendValues} />
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="ld-fg-factors-empty">원천 데이터 없음</div>
              )}
            </details>
          </div>
        </div>
        <FearGreedGauge fearGreed={fearGreed} trend={history?.fearGreed ?? []} tf={tf} />
      </div>
    </div>
  );
}
