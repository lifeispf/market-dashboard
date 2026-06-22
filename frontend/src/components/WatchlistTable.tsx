// Adapted from prototype WatchlistTable.
// Remap: prototype {ind, trig, sig:"open"|"tight", freq} -> contract WatchItem
// {label, trigger, meaning, status:"fired"|"quiet"|"manual_check"|"unknown"}.
// The prototype only rendered ind/trig/sig/freq (4 cols); the contract adds `meaning`
// (no `freq` field) so the table now shows label/trigger/meaning/status (4 cols, status
// replacing the old freq column — freq isn't part of WatchItem per contract.md).
import type { WatchItem, WatchStatus } from "../api/types";

interface WatchlistTableProps {
  watchlist: WatchItem[];
}

const STATUS_LABEL: Record<WatchStatus, string> = {
  fired: "● 발생",
  quiet: "● 평온",
  manual_check: "● 수동확인 필요",
  unknown: "● 불명",
};

export default function WatchlistTable({ watchlist }: WatchlistTableProps) {
  return (
    <div className="ld-section">
      <div className="ld-sec-head">
        <span className="ld-sec-num">F</span>
        <h2 className="ld-h2">통합 워치리스트</h2>
      </div>
      <div className="ld-watch-wrap">
        <table className="ld-table">
          <thead>
            <tr>
              <th>지표</th>
              <th>트리거</th>
              <th>의미</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            {watchlist.map((w, i) => (
              <tr key={i}>
                <td>{w.label}</td>
                <td>{w.trigger}</td>
                <td className="ld-freq" style={{ fontFamily: "inherit", fontSize: 12.5, color: "var(--text-dim)" }}>
                  {w.meaning}
                </td>
                <td className={`sig-${w.status}`}>{STATUS_LABEL[w.status] ?? w.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
