// TimeframeSelector — Phase A. 5-button group (일/주/월/분기/년) styled like the
// market toggle in Header.tsx (`ld-toggle`). Per the plan, only 일(1D)/주(1W) are
// active in Phase A; 월/분기/년 are disabled pending historical backfill, shown
// with a tooltip explaining why.
import type { Timeframe } from "../api/client";

interface TimeframeSelectorProps {
  tf: Timeframe;
  setTf: (tf: Timeframe) => void;
}

const TF_OPTIONS: { key: Timeframe; label: string; enabled: boolean }[] = [
  { key: "1D", label: "일", enabled: true },
  { key: "1W", label: "주", enabled: true },
  { key: "1M", label: "월", enabled: false },
  { key: "1Q", label: "분기", enabled: false },
  { key: "1Y", label: "년", enabled: false },
];

const DISABLED_TOOLTIP = "과거 데이터 백필 후 활성화 예정";

export default function TimeframeSelector({ tf, setTf }: TimeframeSelectorProps) {
  return (
    <div className="ld-toggle ld-tf-toggle">
      {TF_OPTIONS.map((opt) => (
        <button
          key={opt.key}
          className={tf === opt.key ? "active" : ""}
          disabled={!opt.enabled}
          title={opt.enabled ? undefined : DISABLED_TOOLTIP}
          onClick={() => opt.enabled && setTf(opt.key)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
