// Prototype's GlobalMacroBar was 100% hardcoded mock text (Fed Funds, USD/KRW, DXY, HY
// OAS, VIX). The live contract has no top-level "global macro" endpoint/fields — those
// figures are folded into payload.sources[] (S01 Fed, S05 FX, S06 credit) instead.
// Rather than inventing data, this reads the same live payload's source rows so the bar
// reflects real (possibly null) values without violating "no hardcoded market data."
import type { Source } from "../api/types";

interface GlobalMacroBarProps {
  sources: Source[];
}

function findSource(sources: Source[], id: string): Source | undefined {
  return sources.find((s) => s.id === id);
}

export default function GlobalMacroBar({ sources }: GlobalMacroBarProps) {
  const fed = findSource(sources, "S01");
  const fx = findSource(sources, "S05");
  const credit = findSource(sources, "S06");

  return (
    <div className="ld-macro">
      <span>
        중앙은행 정책 <b>{fed?.headroom !== null && fed?.headroom !== undefined ? `헤드룸 ${fed.headroom}/100` : "N/A"}</b>
      </span>
      <span>
        FX 게이트 <b>{fx?.headroom !== null && fx?.headroom !== undefined ? `헤드룸 ${fx.headroom}/100` : "N/A"}</b>
      </span>
      <span>
        글로벌 신용환경 <b>{credit?.headroom !== null && credit?.headroom !== undefined ? `헤드룸 ${credit.headroom}/100` : "N/A"}</b>
      </span>
    </div>
  );
}
