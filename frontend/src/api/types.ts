// FROZEN API contract — mirror of backend/api/contract.md.
// Do not change without updating contract.md and notifying both tracks.

export type Dir = "up" | "down" | "flat";
export type Quadrant = "leading" | "weakening" | "improving" | "lagging";
export type ReconState = "aligned" | "overheated" | "slack";
export type WatchStatus = "fired" | "quiet" | "manual_check" | "unknown";

export interface Flow {
  level: number | null;
  chgPct: number | null;
  yoyPct: number | null;
  fwdPER: number | null;
  trailingPER: number | null;
  breadthText: string | null;
  breadthNote: string | null;
  volLabel: string;
  volValue: number | null;
  volDir: Dir;
  spark: number[];
}

export interface Band { lo: number; hi: number; }
export interface Bands { base: Band; bull: Band; hyper: Band; hyperOpen: boolean; }

export interface Regime { composite: number | null; label: string; nAvailable: number; nTotal: number; }

export interface FearGreedFactor { id: string; name: string; value: number | null; score: number | null; }
export interface FearGreed {
  score: number | null; label: string; nAvailable: number; nTotal: number; factors: FearGreedFactor[];
}

export interface Reconciliation {
  state: ReconState | null; symbol: string; label: string;
  supportedCeiling: number | null; priceBand: string | null; distancePct: number | null;
}

export interface Source {
  id: string; name: string; scope: string; headroom: number | null;
  dir: Dir; dirLabel: string; state: string; score: number | null;
}

export interface Sector {
  code: string; name: string; marketCap: number | null; ytd: number | null;
  rsRatio: number | null; rsMomentum: number | null; quadrant: Quadrant | null;
}

// Minimal RRG-plottable point — generalizes RRGChart's input beyond Sector so it can
// also plot stocks (Phase C: sector-internal stock RRG using Sector-RS coordinates).
// `Sector` already structurally satisfies this (code/name/rsRatio/rsMomentum/quadrant),
// so existing sector RRG usage is unaffected.
export interface RRGPoint {
  code: string;
  name: string;
  rsRatio: number | null;
  rsMomentum: number | null;
  quadrant: Quadrant | null;
}

export interface Leader {
  ticker: string; name: string; role: string; price: number | null; ytd: number | null;
  thesis: string; stats: [string, string][]; risk: string; asOf: string;
}
export interface SectorLeaders { key: Leader[]; star: Leader[]; }

export interface Narrative { flow: string; liquidity: string; leadership: string; reconciliation: string; }
export interface WatchItem { label: string; trigger: string; meaning: string; status: WatchStatus; }
export interface FreshnessItem { label: string; source: string; freq: string; last: string | null; stale: boolean; }

export interface MarketPayload {
  market: "KOSPI" | "NASDAQ";
  asOf: string;
  source: string;
  pill: string;
  flow: Flow;
  bands: Bands | null;
  regime: Regime;
  fearGreed: FearGreed;
  reconciliation: Reconciliation;
  sources: Source[];
  sectors: Sector[];
  leaders: Record<string, SectorLeaders>;
  narrative: Narrative;
  watchlist: WatchItem[];
  freshness: FreshnessItem[];
  _mode: "mock" | "live";
}

// ---------------------------------------------------------------------------
// Engine Core envelope (NOT frozen) — mirror of engine/core/contracts.py.
// Shared shape across all tiers (macro/sector/stock/strategy). Served by the
// new tier endpoints (/api/sectors, later /api/stocks, /api/briefing). This is
// the §8.2 unified envelope the shared primitives (<VerdictCard>/<ModuleCard>)
// render regardless of tier. Distinct from the frozen MarketPayload above.
// ---------------------------------------------------------------------------
export type Direction = "strong_up" | "up" | "neutral" | "down" | "strong_down";
export type Transition = "improving" | "stable" | "weakening" | "breaking";
export type Horizon = "T0" | "T1" | "T2" | "T3";
export type EngineMode = "live" | "mock" | "degraded";

export interface ModuleOutput {
  module_id: string;
  state: string | null;
  transition: Transition | null;
  strength: number | null;
  confidence: number | null;
  narrative: string;
  inputs: Record<string, unknown>;
}

export interface Verdict {
  direction: Direction;
  strength: number; // 0..4
  conviction: number | null;
  lead_pattern: string | null;
  narrative: string;
  risks: string[];
  invalidation: string[];
  horizon: Horizon;
  verified: boolean;
  extra: Record<string, unknown>;
}

export interface EngineOutput {
  tier: string;
  entity_id: string;
  verdict: Verdict;
  modules: ModuleOutput[];
  context: Record<string, unknown>;
  freshness: unknown[];
  mode: EngineMode;
}

export interface SectorsResponse {
  tier: "sector";
  market: "KOSPI" | "NASDAQ";
  sectors: EngineOutput[];
}

export interface StocksResponse {
  tier: "stock";
  market: "KOSPI" | "NASDAQ";
  stocks: EngineOutput[];
}

// ---------------------------------------------------------------------------
// History tier (NOT frozen) — mirror of backend/api/history.py. Sector RRG
// trail (rsRatio/rsMomentum over time) for the trail-overlay feature in
// LeadershipSection/RRGChart. New endpoint added for Phase A timeframes.
// ---------------------------------------------------------------------------
export interface TrailPoint {
  date: string;
  rsRatio: number | null;
  rsMomentum: number | null;
}

export interface SectorTrail {
  code: string;
  trail: TrailPoint[] | null;
}

// Score-trend point (scores_daily / reconstructed F&G) — distinct from TrailPoint
// (which is RRG-specific rsRatio/rsMomentum). Values are 0-100 scores.
export interface ScorePoint {
  date: string;
  value: number;
}

// Phase B — snapshot-indicator score trends. `scores` keys are s01..s06 + composite
// (mirrors backend/api/history.py SCORE_FIELDS); each value degrades independently
// to [] when scores_daily has no/sparse rows for that field. `fearGreed` is
// reconstructed server-side from stored price/vix/oas input series (not persisted
// scores_daily), so it is populated and shows a real trend.
export interface HistoryResponse {
  tier: "history";
  market: "KOSPI" | "NASDAQ";
  tf: string;
  sectors: SectorTrail[];
  scores: Record<string, ScorePoint[]>;
  fearGreed: ScorePoint[];
}
