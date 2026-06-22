import type { MarketPayload } from "./types";

export type Market = "KOSPI" | "NASDAQ";

// Dev: Vite proxies /api → http://localhost:8000 (see vite.config.ts).
export async function fetchMarket(market: Market): Promise<MarketPayload> {
  const res = await fetch(`/api/market/${market}`);
  if (!res.ok) throw new Error(`API ${res.status} for ${market}`);
  return res.json();
}

export interface Health { status: string; db: boolean; fredKey: boolean; krxAuth: boolean; }

export async function fetchHealth(): Promise<Health> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}
