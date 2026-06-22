// Adapted from prototype CrossNarrativeBadge. The prototype computed
// regimeLabel()/reconciliation() client-side from mock composite/bands; the live
// contract instead provides payload.narrative.{flow,liquidity,leadership,reconciliation}
// as server-generated strings (contract.md: "전부 string, 라이브 자동생성") plus
// payload.reconciliation.{symbol,label,distancePct} directly. We render those, with
// graceful "N/A" when distancePct is null (reconciliation.state === null case).
import type { Narrative, Reconciliation } from "../api/types";

interface CrossNarrativeBadgeProps {
  narrative: Narrative;
  rec: Reconciliation;
}

export default function CrossNarrativeBadge({ narrative, rec }: CrossNarrativeBadgeProps) {
  const distLabel =
    rec.distancePct === null || rec.distancePct === undefined
      ? "N/A"
      : `${rec.distancePct >= 0 ? "+" : ""}${rec.distancePct.toFixed(0)}%`;

  return (
    <div className="ld-narrative">
      <span className="ld-narrative-lab">흐름 ▸ 여력 ▸ 주도 ▸ 정합성</span>
      <div className="ld-narrative-row">
        <span className="ld-narrative-seg">
          <b>흐름</b>&nbsp;{narrative.flow || "N/A"}
        </span>
        <span className="ld-narrative-seg">
          <b>여력</b>&nbsp;{narrative.liquidity || "N/A"} (밴드기준 거리 {distLabel})
        </span>
        <span className="ld-narrative-seg">
          <b>주도</b>&nbsp;{narrative.leadership || "N/A"}
        </span>
        <span className="ld-narrative-seg">
          {rec.symbol}&nbsp;<b>정합성</b>&nbsp;{narrative.reconciliation || rec.label || "N/A"}
        </span>
      </div>
    </div>
  );
}
