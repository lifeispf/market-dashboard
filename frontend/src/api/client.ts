import type { MarketPayload, SectorsResponse, StocksResponse } from "./types";

export type Market = "KOSPI" | "NASDAQ";

// Dev: Vite proxies /api → http://localhost:8000 (see vite.config.ts).
export async function fetchMarket(market: Market): Promise<MarketPayload> {
  const res = await fetch(`/api/market/${market}`);
  if (!res.ok) throw new Error(`API ${res.status} for ${market}`);
  return res.json();
}

// Sector tier (Engine Core envelope) — GET /api/sectors/{market}.
export async function fetchSectors(market: Market): Promise<SectorsResponse> {
  const res = await fetch(`/api/sectors/${market}`);
  if (!res.ok) throw new Error(`API ${res.status} for sectors ${market}`);
  return res.json();
}

// Stock tier (Engine Core envelope) — GET /api/stocks/{market}.
export async function fetchStocks(market: Market): Promise<StocksResponse> {
  const res = await fetch(`/api/stocks/${market}`);
  if (!res.ok) throw new Error(`API ${res.status} for stocks ${market}`);
  return res.json();
}

export interface Health { status: string; db: boolean; fredKey: boolean; krxAuth: boolean; }

export async function fetchHealth(): Promise<Health> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}
