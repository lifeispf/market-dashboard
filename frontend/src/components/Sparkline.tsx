// Direct port of prototype Sparkline — pure SVG polyline, no chart deps.
interface SparklineProps {
  data: number[];
  color?: string;
}

export default function Sparkline({ data, color = "var(--brass)" }: SparklineProps) {
  if (!data || data.length < 2) {
    return <div style={{ height: 40, display: "flex", alignItems: "center", color: "var(--text-faint)", fontSize: 11 }}>데이터 없음</div>;
  }
  const w = 100, h = 28;
  const min = Math.min(...data), max = Math.max(...data);
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / (max - min || 1)) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ width: "100%", height: 40 }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.6" />
    </svg>
  );
}
