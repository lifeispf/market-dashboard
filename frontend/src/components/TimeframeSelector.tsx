// TimeframeSelector — Phase A. 5-button group (일/주/월/분기/년) styled like the
// market toggle in Header.tsx (`ld-toggle`). Phase A initially shipped with only
// 일(1D)/주(1W) active pending historical backfill; D-⑥ ran `backend/backfill.py`
// (5yr deep lookback) so 월/분기/년 now have sufficient series_daily depth — all
// 5 buttons are enabled. Per-indicator sparse-data cases still degrade gracefully
// ("데이터 부족") at the chart/sparkline level, so enabling here is safe.
import type { Timeframe } from "../api/client";

interface TimeframeSelectorProps {
  tf: Timeframe;
  setTf: (tf: Timeframe) => void;
}

const TF_OPTIONS: { key: Timeframe; label: string }[] = [
  { key: "1D", label: "일" },
  { key: "1W", label: "주" },
  { key: "1M", label: "월" },
  { key: "1Q", label: "분기" },
  { key: "1Y", label: "년" },
];

export default function TimeframeSelector({ tf, setTf }: TimeframeSelectorProps) {
  return (
    <div className="ld-toggle ld-tf-toggle">
      {TF_OPTIONS.map((opt) => (
        <button key={opt.key} className={tf === opt.key ? "active" : ""} onClick={() => setTf(opt.key)}>
          {opt.label}
        </button>
      ))}
    </div>
  );
}
