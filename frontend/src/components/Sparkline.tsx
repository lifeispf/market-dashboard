// Direct port of prototype Sparkline — pure SVG polyline, no chart deps.
// Extended (non-breaking) with an optional `showStats` mode that adds endpoint
// labels, a last-point marker, min/max dashed reference lines, and direction
// coloring — purely additive, default usage (no showStats) renders identically
// to before.
interface SparklineProps {
  data: number[];
  color?: string;
  showStats?: boolean;
}

export default function Sparkline({ data, color, showStats = false }: SparklineProps) {
  if (!data || data.length < 2) {
    return <div style={{ height: 40, display: "flex", alignItems: "center", color: "var(--text-faint)", fontSize: 11 }}>데이터 없음</div>;
  }
  const w = 100, h = 28;
  const min = Math.min(...data), max = Math.max(...data);
  const first = data[0];
  const last = data[data.length - 1];
  const up = last >= first;
  const lineColor = color ?? (showStats ? (up ? "var(--open)" : "var(--tight)") : "var(--brass)");

  const xAt = (i: number) => (i / (data.length - 1)) * w;
  const yAt = (v: number) => h - ((v - min) / (max - min || 1)) * h;

  const pts = data.map((v, i) => `${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`).join(" ");

  if (!showStats) {
    return (
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: "100%", height: 40 }}>
        <polyline points={pts} fill="none" stroke={lineColor} strokeWidth="1.6" />
      </svg>
    );
  }

  const lastX = xAt(data.length - 1);
  const lastY = yAt(last);
  const minY = yAt(min);
  const maxY = yAt(max);

  return (
    <div className="ld-spark-stats">
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: "100%", height: 40 }}>
        {/* range reference lines (min/max) */}
        <line x1={0} y1={maxY} x2={w} y2={maxY} className="ld-spark-refline" />
        <line x1={0} y1={minY} x2={w} y2={minY} className="ld-spark-refline" />
        <polyline points={pts} fill="none" stroke={lineColor} strokeWidth="1.6" />
        {/* last point marker */}
        <circle cx={lastX} cy={lastY} r={2.2} fill={lineColor} />
      </svg>
      <div className="ld-spark-minmax">
        <span className="ld-spark-maxlab">max {max.toLocaleString()}</span>
        <span className="ld-spark-minlab">min {min.toLocaleString()}</span>
      </div>
      <div className="ld-spark-endpoints">
        <span className="ld-spark-ep ld-spark-ep-first">{first.toLocaleString()}</span>
        <span className="ld-spark-ep ld-spark-ep-last">{last.toLocaleString()}</span>
      </div>
    </div>
  );
}
