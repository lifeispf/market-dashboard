import type { HistoryResponse, MarketPayload, SectorsResponse, StocksResponse } from "./types";

export type Market = "KOSPI" | "NASDAQ";

// Timeframe bundle key — mirrors engine/core/timeframes.py TIMEFRAMES. 1D=일,
// 1W=주, 1M=월, 1Q=분기, 1Y=년. Default "1D" is byte-identical to pre-tf behavior.
export type Timeframe = "1D" | "1W" | "1M" | "1Q" | "1Y";

// Dev: Vite proxies /api → http://localhost:8000 (see vite.config.ts).
export async function fetchMarket(market: Market, tf: Timeframe = "1D"): Promise<MarketPayload> {
  const res = await fetch(`/api/market/${market}?tf=${tf}`);
  if (!res.ok) throw new Error(`API ${res.status} for ${market}`);
  return res.json();
}

// Sector tier (Engine Core envelope) — GET /api/sectors/{market}.
export async function fetchSectors(market: Market, tf: Timeframe = "1D"): Promise<SectorsResponse> {
  const res = await fetch(`/api/sectors/${market}?tf=${tf}`);
  if (!res.ok) throw new Error(`API ${res.status} for sectors ${market}`);
  return res.json();
}

// Stock tier (Engine Core envelope) — GET /api/stocks/{market}.
export async function fetchStocks(market: Market, tf: Timeframe = "1D"): Promise<StocksResponse> {
  const res = await fetch(`/api/stocks/${market}?tf=${tf}`);
  if (!res.ok) throw new Error(`API ${res.status} for stocks ${market}`);
  return res.json();
}

// History tier (sector RRG trail) — GET /api/history/{market}?tf=.
export async function fetchHistory(market: Market, tf: Timeframe = "1D"): Promise<HistoryResponse> {
  const res = await fetch(`/api/history/${market}?tf=${tf}`);
  if (!res.ok) throw new Error(`API ${res.status} for history ${market}`);
  return res.json();
}

export interface Health { status: string; db: boolean; fredKey: boolean; krxAuth: boolean; }

export async function fetchHealth(): Promise<Health> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}
