// Adapted from planning/market-dashboard-prototype.jsx helpers.
// Differences vs prototype:
//  - bands/composite/reconciliation may be null (live backend has no FRED/KRX keys) -> all helpers are null-safe.
//  - rsRatio/rsMomentum from the live contract are centered on 100 (not 1.0 / 0 like the prototype's mock rsR/rsM),
//    so quadrant comes pre-computed from the server (payload.sectors[].quadrant) and is NOT recomputed client-side.

import type { Bands, Direction, Quadrant, Transition } from "../api/types";

export const fmt = (n: number | null | undefined): string => {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  return Math.round(n).toLocaleString();
};

export const fmtPct = (n: number | null | undefined, digits = 0): string => {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  const s = n.toFixed(digits);
  return n >= 0 ? `+${s}%` : `${s}%`;
};

export const fmtNum = (n: number | null | undefined, digits = 1): string => {
  if (n === null || n === undefined || Number.isNaN(n)) return "N/A";
  return n.toFixed(digits);
};

export function regimeLabel(composite: number | null, fallback?: string): string {
  if (composite === null || composite === undefined) return fallback ?? "산정 불가";
  if (composite >= 67) return "HYPER 연료 존재";
  if (composite >= 34) return "BULL 도달가능";
  return "BASE only";
}

export function allowedRank(composite: number | null): number | null {
  if (composite === null || composite === undefined) return null;
  if (composite >= 67) return 3;
  if (composite >= 34) return 2;
  return 1;
}

export function rank(value: number | null, bands: Bands | null): number | null {
  if (value === null || value === undefined || !bands) return null;
  if (value >= bands.hyper.lo) return 3;
  if (value >= bands.bull.lo) return 2;
  if (value >= bands.base.lo) return 1;
  return 0;
}

export const bandName = (r: number | null): string => {
  if (r === null || r === undefined) return "N/A";
  return r === 3 ? "HYPER" : r === 2 ? "BULL" : r === 1 ? "BASE" : "BASE 미달";
};

export const QUAD_COLOR: Record<Quadrant, string> = {
  leading: "open",
  weakening: "tight",
  improving: "neutral",
  lagging: "locked",
};
export const QUAD_KR: Record<Quadrant, string> = {
  leading: "주도 지속",
  weakening: "차익 임박",
  improving: "순환매 진입",
  lagging: "소외",
};

export function quadColor(q: Quadrant | null): string {
  if (!q) return "locked";
  return QUAD_COLOR[q];
}
export function quadKr(q: Quadrant | null): string {
  if (!q) return "분류 불가";
  return QUAD_KR[q];
}

// headroom/score (0-100|null) -> brass-system color bucket used for fill bars
export function headroomColor(v: number | null): string {
  if (v === null || v === undefined) return "locked";
  if (v >= 60) return "open";
  if (v >= 40) return "neutral";
  return "tight";
}

// Fear & Greed score (0-100|null) -> distinct "심리" palette bucket (fg-open=fear/blue, fg-neutral=neutral/violet, fg-tight=greed/magenta)
// Reuses the .fg-* fill classes defined in styles.css, kept structurally parallel to f-* but a different hue family.
export function fearGreedColor(score: number | null): string {
  if (score === null || score === undefined) return "neutral";
  if (score >= 55) return "tight"; // greed end -> fg-tight (magenta)
  if (score <= 45) return "open"; // fear end -> fg-open (blue)
  return "neutral";
}

// ---- Engine Core envelope display helpers (tier-agnostic) ----

// Verdict.direction -> brass-system color bucket (open=green/up, neutral=gold, tight=red/down).
export function directionColor(d: Direction): string {
  if (d === "strong_up" || d === "up") return "open";
  if (d === "strong_down" || d === "down") return "tight";
  return "neutral";
}

export const DIRECTION_KR: Record<Direction, string> = {
  strong_up: "강한 상승",
  up: "상승",
  neutral: "중립",
  down: "하락",
  strong_down: "강한 하락",
};

export const DIRECTION_ARROW: Record<Direction, string> = {
  strong_up: "▲▲",
  up: "▲",
  neutral: "—",
  down: "▼",
  strong_down: "▼▼",
};

export const TRANSITION_KR: Record<Transition, string> = {
  improving: "개선",
  stable: "안정",
  weakening: "둔화",
  breaking: "붕괴",
};

export function transitionKr(t: Transition | null): string {
  if (!t) return "추세 불명";
  return TRANSITION_KR[t];
}
