// Adapted from prototype CeilingChart. Live backend has no EPS input -> bands is
// frequently null (see contract.md: "EPS 미입력 시 bands: null"). Render a clean
// empty state instead of crashing or guessing band values.
//
// D-②: engine/macro/eps_source.py now derives a forward EPS *estimate* from an
// ETF-proxy forward PE (not consensus EPS) so bands can light up without a paid
// data source. The frozen payload doesn't expose which EPS source was used, so
// whenever bands are non-null we show a static caveat — accurate for this setup
// since EPS is always proxy-derived here, never consensus.
import { fmt } from "../lib/helpers";
import type { Bands } from "../api/types";

interface CeilingChartProps {
  bands: Bands | null;
  current: number | null;
  supported: number | null;
}

export default function CeilingChart({ bands, current, supported }: CeilingChartProps) {
  if (!bands || current === null || current === undefined) {
    return (
      <div className="ceilbox">
        <div className="ld-empty">
          시나리오별 천장 밴드 산정 불가
          <br />
          (EPS 입력값 미입력 — bands: null)
        </div>
      </div>
    );
  }

  const min = Math.min(current, bands.base.lo) * 0.92;
  const max = bands.hyper.hi * 1.12;
  const pct = (v: number) => Math.max(0, Math.min(100, ((max - v) / (max - min)) * 100));
  const order = [
    { key: "hyper", lo: bands.hyper.lo, hi: bands.hyper.hi, cls: "tight", name: "HYPER", open: bands.hyperOpen },
    { key: "bull", lo: bands.bull.lo, hi: bands.bull.hi, cls: "neutral", name: "BULL", open: false },
    { key: "base", lo: bands.base.lo, hi: bands.base.hi, cls: "open", name: "BASE", open: false },
  ];

  return (
    <div className="ceilbox">
      <div className="ceilplot">
        {order.map((b) => (
          <div key={b.key} className={`band band-${b.cls}`} style={{ top: pct(b.hi) + "%", height: pct(b.lo) - pct(b.hi) + "%" }}>
            <span className="band-label">
              {b.name} {fmt(b.lo)}–{fmt(b.hi)}
              {b.open ? "+" : ""}
            </span>
          </div>
        ))}
        {supported !== null && supported !== undefined && (
          <div className="supline" style={{ top: pct(supported) + "%" }}>
            <span className="supline-label">유동성 지지 천장 {fmt(supported)}</span>
          </div>
        )}
        <div className="curline" style={{ top: pct(current) + "%" }}>
          <span className="curline-label">현재 {fmt(current)}</span>
        </div>
      </div>
      <div className="ld-eps-caveat">선행 EPS는 ETF 프록시 기반 추정치 (컨센서스 아님)</div>
    </div>
  );
}
