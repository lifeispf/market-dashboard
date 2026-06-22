// Direct field-name match: prototype data.flow.* === payload.flow.* (Flow interface in
// types.ts mirrors the prototype's mock shape almost 1:1). Main change is null-safety:
// fwdPER/trailingPER/breadthText/breadthNote/chgPct/yoyPct/volValue are all nullable on
// the live backend (no FRED/KRX keys -> breadth fields are null; PER fields need EPS).
import { DirIcon } from "./icons";
import Sparkline from "./Sparkline";
import { fmt, fmtPct, fmtNum } from "../lib/helpers";
import type { Flow } from "../api/types";

interface FlowSectionProps {
  flow: Flow;
}

export default function FlowSection({ flow }: FlowSectionProps) {
  const chgUp = (flow.chgPct ?? 0) >= 0;
  const volUp = flow.volDir === "up";

  return (
    <div className="ld-section">
      <div className="ld-sec-head">
        <span className="ld-sec-num">LAYER 1</span>
        <h2 className="ld-h2">흐름</h2>
      </div>
      <p className="ld-sec-sub">지금 지수가 어디서 · 어떻게 움직이는지 — 가격, breadth, 변동성.</p>
      <div className="ld-kpis">
        <div className="ld-kpi">
          <div className="l">현재가</div>
          <div className="v">{fmt(flow.level)}</div>
          <div className={`c c-${flow.chgPct === null ? "flat" : chgUp ? "up" : "down"}`}>
            {flow.chgPct !== null && <DirIcon dir={chgUp ? "up" : "down"} />}
            {flow.chgPct === null ? "N/A" : `${fmtPct(flow.chgPct, 2)} (1D)`}
          </div>
        </div>
        <div className="ld-kpi">
          <div className="l">YoY</div>
          <div className="v">{flow.yoyPct === null ? "N/A" : fmtPct(flow.yoyPct, 0)}</div>
          <div className="c c-flat">52주 변동</div>
        </div>
        <div className="ld-kpi">
          <div className="l">선행 PER</div>
          <div className="v">{flow.fwdPER === null ? "N/A" : `${fmtNum(flow.fwdPER)}x`}</div>
          <div className="c c-flat">{flow.trailingPER === null ? "trailing N/A" : `trailing ${fmtNum(flow.trailingPER)}x`}</div>
        </div>
        <div className="ld-kpi">
          <div className="l">Breadth</div>
          <div className="v" style={{ fontSize: 15 }}>
            {flow.breadthText || "N/A"}
          </div>
          <div className="c c-flat">{flow.breadthNote || "데이터 없음"}</div>
        </div>
        <div className="ld-kpi">
          <div className="l">{flow.volLabel}</div>
          <div className="v">{flow.volValue === null ? "N/A" : fmtNum(flow.volValue)}</div>
          <div className={`c c-${volUp ? "down" : "up"}`}>
            <DirIcon dir={flow.volDir} />
            {flow.volDir === "down" ? "안정화" : flow.volDir === "up" ? "상승" : "변동 없음"}
          </div>
        </div>
      </div>
      <div className="ld-spark-wrap">
        <div className="ld-spark-lab">최근 추세 (상대 형태)</div>
        <Sparkline data={flow.spark} />
      </div>
    </div>
  );
}
