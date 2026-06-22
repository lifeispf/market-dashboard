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
