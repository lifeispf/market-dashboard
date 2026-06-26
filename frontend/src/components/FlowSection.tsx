// Direct field-name match: prototype data.flow.* === payload.flow.* (Flow interface in
// types.ts mirrors the prototype's mock shape almost 1:1). Main change is null-safety:
// fwdPER/trailingPER/breadthText/breadthNote/chgPct/yoyPct/volValue are all nullable on
// the live backend (no FRED/KRX keys -> breadth fields are null; PER fields need EPS).
import { DirIcon } from "./icons";
import Sparkline from "./Sparkline";
import { fmt, fmtPct, fmtNum } from "../lib/helpers";
import type { Flow } from "../api/types";
import type { Timeframe } from "../api/client";

interface FlowSectionProps {
  flow: Flow;
  tf: Timeframe;
}

// tf-specific spark label + window wording (per plan §FlowSection — spark data itself
// already arrives tf-correct from the payload; this just relabels the candle cadence).
const SPARK_LABEL: Record<Timeframe, string> = {
  "1D": "최근 추세 · 일봉",
  "1W": "최근 추세 · 주봉",
  "1M": "최근 추세 · 월봉",
  "1Q": "최근 추세 · 분기봉",
  "1Y": "최근 추세 · 연봉",
};

// Breadth 해석(5등급/Lv1~5) — backend breadthNote는 라이브 엔진이 안 채우므로(잔재 필드,
// 항상 null) 같은 payload의 breadthText("상승 X · 하락 Y" / "섹터 N개 상승 · M개 하락")에서
// 상승/하락 수를 파싱해 상승비율을 5구간으로 해석한다. 동결 payload·등가성 게이트 무관.
// 비율 대칭(±20% 강·±8% 중립) — 대시보드 F&G 5존과 일관된 등급 수. 색은 Lv1 빨강 →
// Lv5 초록 그라데이션(주황·노랑·연두 경유).
function interpretBreadth(
  breadthText: string | null,
): { lv: number; label: string; text: string; color: string; pct: number } | null {
  if (!breadthText) return null;
  const nums = breadthText.match(/\d+/g);
  if (!nums || nums.length < 2) return null;
  const up = parseInt(nums[0], 10);
  const down = parseInt(nums[1], 10);
  if (up + down === 0) return null;
  const pct = Math.round((up / (up + down)) * 100);
  if (pct >= 70) return { lv: 5, label: "매우 강함", text: "광범위 동반 상승", color: "#4caf78", pct };
  if (pct >= 58) return { lv: 4, label: "강함", text: "상승 우위", color: "#9bcf5a", pct };
  if (pct >= 42) return { lv: 3, label: "중립", text: "혼조 · 방향성 약함", color: "#dcc24e", pct };
  if (pct >= 30) return { lv: 2, label: "약함", text: "하락 우위", color: "#e09a4a", pct };
  return { lv: 1, label: "매우 약함", text: "광범위 동반 하락", color: "#d75f4f", pct };
}

export default function FlowSection({ flow, tf }: FlowSectionProps) {
  const chgUp = (flow.chgPct ?? 0) >= 0;
  const volUp = flow.volDir === "up";

  // window % change over the spark series itself (NOT flow.chgPct, which is 1D) —
  // spark[last]/spark[0] - 1, null-safe when spark is too short.
  const spark = flow.spark;
  const hasSpark = !!spark && spark.length >= 2;
  const sparkFirst = hasSpark ? spark[0] : null;
  const sparkLast = hasSpark ? spark[spark.length - 1] : null;
  const sparkWindowPct = hasSpark && sparkFirst !== null && sparkFirst !== 0 ? (sparkLast! / sparkFirst! - 1) * 100 : null;
  const sparkUp = (sparkWindowPct ?? 0) >= 0;

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
          {(() => {
            // breadthNote(서버)가 있으면 그대로, 없으면 breadthText에서 상승비율을 5등급 해석.
            if (flow.breadthNote) return <div className="c c-flat">{flow.breadthNote}</div>;
            const b = interpretBreadth(flow.breadthText);
            if (!b) return <div className="c c-flat">데이터 없음</div>;
            return (
              <div className="c" style={{ color: b.color }} title={`상승비율 ${b.pct}%`}>
                Lv{b.lv} {b.label} · {b.text}
              </div>
            );
          })()}
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
        <div className="ld-spark-head">
          <div className="ld-spark-lab">{SPARK_LABEL[tf]} · 상대형태(절대값 아님)</div>
          {sparkWindowPct !== null && (
            <span className={`ld-spark-badge c-${sparkUp ? "up" : "down"}`}>
              <DirIcon dir={sparkUp ? "up" : "down"} size={10} />
              {fmtPct(sparkWindowPct, 1)} (창 구간)
            </span>
          )}
        </div>
        <Sparkline data={flow.spark} showStats />
      </div>
    </div>
  );
}
