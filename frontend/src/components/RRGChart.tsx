// Adapted from prototype RRGChart.
// KEY DIFFERENCE vs prototype: the live contract's rsRatio/rsMomentum are centered on
// 100 (e.g. 99.5, 101.7), not on 1.0 / 0 like the prototype's mock rsR/rsM. The center
// crosshair and axis domain below are rebuilt around 100/100 instead of 1.0/0.
// quadrant is pre-computed server-side (payload.sectors[].quadrant) — not recomputed here.
import { QUAD_COLOR } from "../lib/helpers";
import type { Sector } from "../api/types";

interface RRGChartProps {
  sectors: Sector[];
  selectedKey: string | null;
  onSelect: (code: string) => void;
}

export default function RRGChart({ sectors, selectedKey, onSelect }: RRGChartProps) {
  const plottable = sectors.filter((s) => s.rsRatio !== null && s.rsMomentum !== null);

  if (plottable.length === 0) {
    return (
      <div className="rrgbox">
        <div className="rrgplot">
          <div className="ld-empty">RRG 데이터 없음 (rsRatio/rsMomentum 미가용)</div>
        </div>
      </div>
    );
  }

  const xs = plottable.map((s) => s.rsRatio as number);
  const ys = plottable.map((s) => s.rsMomentum as number);
  // Center the domain on 100 (the live RS-ratio/RS-momentum benchmark), padding outward
  // to fit outliers — mirrors the prototype's "pad beyond 1.0/0 center" approach.
  const xSpread = Math.max(8, ...xs.map((v) => Math.abs(v - 100))) * 1.15;
  const ySpread = Math.max(8, ...ys.map((v) => Math.abs(v - 100))) * 1.15;
  const xmin = 100 - xSpread, xmax = 100 + xSpread;
  const ymin = 100 - ySpread, ymax = 100 + ySpread;
  const leftPct = (v: number) => ((v - xmin) / (xmax - xmin)) * 100;
  const topPct = (v: number) => ((ymax - v) / (ymax - ymin)) * 100;
  const xZero = leftPct(100), yZero = topPct(100);

  return (
    <div className="rrgbox">
      <div className="rrgplot">
        <div className="rrg-quad" style={{ position: "absolute", left: xZero + "%", top: 0, right: 0, height: yZero + "%" }}>
          <span style={{ top: 0, right: 0 }}>LEADING</span>
        </div>
        <div className="rrg-quad" style={{ position: "absolute", left: xZero + "%", top: yZero + "%", right: 0, bottom: 0 }}>
          <span style={{ bottom: 0, right: 0 }}>WEAKENING</span>
        </div>
        <div className="rrg-quad" style={{ position: "absolute", left: 0, top: 0, width: xZero + "%", height: yZero + "%" }}>
          <span style={{ top: 0, left: 0 }}>IMPROVING</span>
        </div>
        <div className="rrg-quad" style={{ position: "absolute", left: 0, top: yZero + "%", width: xZero + "%", bottom: 0 }}>
          <span style={{ bottom: 0, left: 0 }}>LAGGING</span>
        </div>
        <div className="rrg-axis-x" style={{ left: xZero + "%" }} />
        <div className="rrg-axis-y" style={{ top: yZero + "%" }} />
        {plottable.map((s) => {
          const color = QUAD_COLOR[s.quadrant ?? "lagging"];
          return (
            <button
              key={s.code}
              className={`rrg-dot dot-${color} ${selectedKey === s.code ? "sel" : ""}`}
              style={{ left: leftPct(s.rsRatio as number) + "%", top: topPct(s.rsMomentum as number) + "%" }}
              onClick={() => onSelect(s.code)}
              title={s.name}
            >
              <span className="rrg-dot-label">{s.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
