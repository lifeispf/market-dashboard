// VerificationPanel (Phase F) — consumes GET /api/verification/{market}, the
// full-history (tf-independent) scorecard that turns the dashboard's signals
// from "비검증 휴리스틱" into measured evidence: walk-forward-free IC / hit-rate
// / sample-size stats computed once over backfilled history. Self-fetches like
// SectorView/StockView; takes only `market` as a prop.
import { useEffect, useState } from "react";
import { fetchVerification, type Market } from "../api/client";
import type {
  ErrorSection,
  FgExtremeHorizon,
  FgExtremes,
  MomentumIc,
  RegimeFactorIc,
  RrgHitRate,
  Scorecard,
} from "../api/types";

interface VerificationPanelProps {
  market: Market;
}

function isErrorSection(v: unknown): v is ErrorSection {
  return !!v && typeof v === "object" && "error" in (v as Record<string, unknown>);
}

function fmtN(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  return n.toLocaleString();
}

function fmtPctSigned(n: number | null | undefined, digits = 2): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  const s = n.toFixed(digits);
  return n >= 0 ? `+${s}%` : `${s}%`;
}

function fmtPctPlain(n: number | null | undefined, digits = 1): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  return `${n.toFixed(digits)}%`;
}

function fmtIc(n: number | null | undefined, digits = 3): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  return n.toFixed(digits);
}

// |ic|<0.05 -> neutral (weak/no signal), ic>=0.05 -> green (유효, predicts as expected),
// ic<=-0.05 -> red (역방향 — predicts opposite of expected sign).
function icColor(ic: number | null | undefined): string {
  if (ic === null || ic === undefined || Number.isNaN(ic)) return "vp-neutral";
  if (ic >= 0.05) return "vp-open";
  if (ic <= -0.05) return "vp-tight";
  return "vp-neutral";
}

// Hit-rate vs 50% coin-flip baseline: >55% green (유효), <45% red (역방향), else neutral (약한 신호).
function hitRateColor(hr: number | null | undefined): string {
  if (hr === null || hr === undefined || Number.isNaN(hr)) return "vp-neutral";
  if (hr > 55) return "vp-open";
  if (hr < 45) return "vp-tight";
  return "vp-neutral";
}

function SampleN({ n }: { n: number | null | undefined }) {
  return <span className="vp-n">n={fmtN(n)}</span>;
}

function ErrorNote({ section }: { section: ErrorSection }) {
  return <div className="vp-error-note">산정 불가 — {section.error}</div>;
}

function FgExtremesCard({ data }: { data: FgExtremes | ErrorSection }) {
  if (isErrorSection(data)) {
    return (
      <div className="vp-card">
        <div className="vp-card-head">
          <span className="vp-card-title">F&amp;G 극단 → 반전</span>
        </div>
        <ErrorNote section={data} />
      </div>
    );
  }
  const horizons = Object.keys(data).sort((a, b) => Number(a) - Number(b));
  return (
    <div className="vp-card">
      <div className="vp-card-head">
        <span className="vp-card-title">F&amp;G 극단 → 반전</span>
        <span className="vp-card-hint">공포에서 양전률 높을수록 컨트래리언 유효</span>
      </div>
      {horizons.length === 0 ? (
        <div className="vp-empty">데이터 없음</div>
      ) : (
        <div className="vp-fg-grid">
          {horizons.map((h) => {
            const entry: FgExtremeHorizon = data[h];
            return (
              <div key={h} className="vp-fg-horizon">
                <div className="vp-fg-horizon-label">h={h}일</div>
                <div className="vp-fg-row">
                  <span className="vp-fg-side-label vp-open-text">공포(≤25)</span>
                  <span className="vp-fg-stat">
                    향후수익 {fmtPctSigned(entry.fear?.mean_fwd_ret_pct)} · 양전률{" "}
                    {fmtPctPlain(entry.fear?.pct_positive)}
                  </span>
                  <SampleN n={entry.fear?.n} />
                </div>
                <div className="vp-fg-row">
                  <span className="vp-fg-side-label vp-tight-text">탐욕(≥75)</span>
                  <span className="vp-fg-stat">
                    향후수익 {fmtPctSigned(entry.greed?.mean_fwd_ret_pct)} · 음전률{" "}
                    {fmtPctPlain(entry.greed?.pct_negative)}
                  </span>
                  <SampleN n={entry.greed?.n} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function RrgHitRateCard({ data }: { data: RrgHitRate | ErrorSection }) {
  if (isErrorSection(data)) {
    return (
      <div className="vp-card">
        <div className="vp-card-head">
          <span className="vp-card-title">섹터 RRG 적중률</span>
        </div>
        <ErrorNote section={data} />
      </div>
    );
  }
  return (
    <div className="vp-card">
      <div className="vp-card-head">
        <span className="vp-card-title">섹터 RRG 적중률</span>
        <span className="vp-card-hint">
          기준선 50% (동전 던지기) · h={fmtN(data.horizon_days)}일 · 단일윈도우 RRG는 약한 예측력
        </span>
      </div>
      <div className="vp-rrg-grid">
        <div className="vp-rrg-row">
          <span className="vp-rrg-label">Bullish (Leading/Improving)</span>
          <span className={`vp-rrg-val ${hitRateColor(data.hit_rate_bullish)}`}>
            {fmtPctPlain(data.hit_rate_bullish)}
          </span>
          <SampleN n={data.n_bullish} />
        </div>
        <div className="vp-rrg-row">
          <span className="vp-rrg-label">Bearish (Weakening/Lagging)</span>
          <span className={`vp-rrg-val ${hitRateColor(data.hit_rate_bearish)}`}>
            {fmtPctPlain(data.hit_rate_bearish)}
          </span>
          <SampleN n={data.n_bearish} />
        </div>
      </div>
    </div>
  );
}

function MomentumIcCard({ data }: { data: MomentumIc | ErrorSection }) {
  if (isErrorSection(data)) {
    return (
      <div className="vp-card">
        <div className="vp-card-head">
          <span className="vp-card-title">모멘텀 IC</span>
        </div>
        <ErrorNote section={data} />
      </div>
    );
  }
  return (
    <div className="vp-card">
      <div className="vp-card-head">
        <span className="vp-card-title">모멘텀 IC</span>
      </div>
      <div className="vp-ic-row">
        <span className={`vp-ic-val ${icColor(data.ic)}`}>IC {fmtIc(data.ic)}</span>
        <SampleN n={data.n} />
      </div>
      {data.desc && <div className="vp-card-desc">{data.desc}</div>}
    </div>
  );
}

function RegimeFactorIcCard({ data }: { data: RegimeFactorIc | ErrorSection }) {
  if (isErrorSection(data)) {
    return (
      <div className="vp-card">
        <div className="vp-card-head">
          <span className="vp-card-title">Regime 팩터 IC + 가중치 제안</span>
        </div>
        <ErrorNote section={data} />
      </div>
    );
  }
  const factorKeys = data.factors ? Object.keys(data.factors).sort() : [];
  const current = data.current_weights_subset;
  const suggested = data.suggested_weights_subset;
  return (
    <div className="vp-card">
      <div className="vp-card-head">
        <span className="vp-card-title">Regime 팩터 IC + 가중치 제안</span>
        <span className="vp-card-hint">제안 가중치는 자동 적용되지 않음 — 참고용</span>
      </div>
      {factorKeys.length === 0 ? (
        <div className="vp-empty">데이터 없음</div>
      ) : (
        <table className="vp-factor-table">
          <thead>
            <tr>
              <th>팩터</th>
              <th>IC</th>
              <th>n</th>
              <th>현재 가중</th>
              <th>제안 가중</th>
            </tr>
          </thead>
          <tbody>
            {factorKeys.map((k) => {
              const f = data.factors![k];
              return (
                <tr key={k}>
                  <td className="vp-factor-id">{k}</td>
                  <td className={icColor(f.ic)}>{fmtIc(f.ic)}</td>
                  <td className="vp-factor-n">{fmtN(f.n)}</td>
                  <td className="vp-factor-n">{current && current[k] !== undefined ? current[k].toFixed(2) : "N/A"}</td>
                  <td className="vp-factor-n">
                    {suggested && suggested[k] !== undefined ? suggested[k].toFixed(2) : "N/A"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      {data.note && <div className="vp-card-desc">{data.note}</div>}
    </div>
  );
}

export default function VerificationPanel({ market }: VerificationPanelProps) {
  const [scorecard, setScorecard] = useState<Scorecard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setScorecard(null);
    setError(null);
    fetchVerification(market)
      .then((res) => {
        if (cancelled) return;
        setScorecard(res.scorecard);
      })
      .catch((e) => {
        if (cancelled) return;
        setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [market]);

  return (
    <div className="ld-section">
      <div className="ld-sec-head">
        <span className="ld-sec-num">VERIFICATION TIER</span>
        <h2 className="ld-h2">신호 신뢰도 (검증)</h2>
      </div>
      <p className="ld-sec-sub">
        대시보드 신호들의 측정된 신뢰도 — 백필된 전구간 데이터에서 계산한 IC(정보계수)·적중률·표본수.
        워크포워드 검증이 아닌 전구간(in-sample) 통계이므로 참고 지표로 활용.
      </p>

      {error && <div className="sv-msg" style={{ color: "var(--tight)" }}>⚠ 검증 API 실패: {error}</div>}
      {!error && scorecard === null && <div className="sv-msg">검증 스코어카드 불러오는 중…</div>}

      {scorecard && (
        <>
          <div className="vp-grid">
            <FgExtremesCard data={scorecard.fear_greed_extremes} />
            <RrgHitRateCard data={scorecard.sector_rrg_hit_rate} />
            <MomentumIcCard data={scorecard.momentum_ic} />
            <RegimeFactorIcCard data={scorecard.regime_factor_ic} />
          </div>
          <div className="vp-footnote">
            <div className="vp-footnote-head">
              <span>한계 (Limitations)</span>
              <span className="vp-footnote-n">지수 표본 n={fmtN(scorecard.index_sample_n)}</span>
            </div>
            <div className="vp-footnote-text">{scorecard.limitations ?? "N/A"}</div>
          </div>
        </>
      )}
    </div>
  );
}
