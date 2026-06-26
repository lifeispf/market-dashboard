// LAYER 0 — Executive Summary (5초 시장 진단). Decision Intelligence의 What→Why 진입점.
// 데이터는 /api/briefing(룰베이스 캐스케이드 + Layer0 합성). 헤드라인 + 4줄(상태/체력/
// 여력/전략) + 펼치면 Why(narrative) & 찬성↔반대 근거(supports vs risks = 룰베이스 Debate)
// + 무효화 조건. 신뢰도는 verified 게이트(§9.1)대로 "비검증 휴리스틱"으로 정직 표기 —
// 가짜 % confidence를 쓰지 않는다(프로젝트 정직성 기조).
import type { BriefingResponse } from "../api/types";

const TONE_COLOR: Record<string, string> = {
  up: "var(--open)",
  down: "var(--tight)",
  flat: "var(--text-dim)",
};

export default function ExecutiveSummary({ briefing }: { briefing: BriefingResponse }) {
  const { summary, macro } = briefing;
  const v = macro?.verdict;
  const supports = (v?.extra?.supports as string[] | undefined) ?? [];
  const risks = v?.risks ?? [];
  const invalidation = v?.invalidation ?? [];

  return (
    <div className="ld-exec">
      <div className="ld-exec-head">
        <span className="ld-exec-tag">LAYER 0 · 한눈에</span>
        <span className="ld-exec-headline">{summary.headline}</span>
      </div>

      <div className="ld-exec-lines">
        {summary.lines.map((ln) => (
          <div className="ld-exec-line" key={ln.label}>
            <span className="ld-exec-label">{ln.label}</span>
            <span className="ld-exec-value" style={{ color: TONE_COLOR[ln.tone] }}>
              {ln.value}
            </span>
          </div>
        ))}
      </div>

      <details className="ld-exec-why">
        <summary>왜? · 근거 (찬성 ↔ 반대)</summary>
        {v?.narrative && <div className="ld-exec-narr">{v.narrative}</div>}
        <div className="ld-exec-debate">
          <div className="ld-exec-col">
            <div className="ld-exec-col-h up">찬성 근거</div>
            {supports.length ? (
              supports.map((s, i) => (
                <div className="ld-exec-pt up" key={i}>
                  + {s}
                </div>
              ))
            ) : (
              <div className="ld-exec-empty">—</div>
            )}
          </div>
          <div className="ld-exec-col">
            <div className="ld-exec-col-h down">반대 근거 (Counter)</div>
            {risks.length ? (
              risks.map((r, i) => (
                <div className="ld-exec-pt down" key={i}>
                  − {r}
                </div>
              ))
            ) : (
              <div className="ld-exec-empty">—</div>
            )}
          </div>
        </div>
        {invalidation.length > 0 && (
          <div className="ld-exec-invalid">
            <b>무효화 조건</b> · {invalidation.join(" · ")}
          </div>
        )}
        <div className="ld-exec-caveat">
          룰베이스 추론 · 비검증 휴리스틱(walk-forward 전) — 측정 팩터에서 규칙 생성, 투자자문 아님
        </div>
      </details>
    </div>
  );
}
