"""backend/backfill.py — one-time idempotent historical backfill (Phase D-⑥).

Problem: series_daily currently holds ~1.6yr of daily data, which starves the
월/분기/년 (monthly/quarterly/yearly) timeframes and the verification harness
of history. This script deepens history (default 5yr) by re-running the
EXISTING fetchers (via backend/store/series_map.build_registry) with a much
longer lookback and writing through the EXISTING public db.upsert_series API.

Guardrails (do not violate):
  - Does NOT modify backend/store/*, data/*, scoring.py, scoring_ext.py,
    config.json, sectors.json. Only CALLS their public functions.
  - Idempotent: db.upsert_series is ON CONFLICT(series_id, date) DO UPDATE, so
    re-running this script never corrupts existing rows — it only deepens/
    refreshes them.
  - Never lets one series' failure abort the run: every fetch+upsert is
    wrapped in try/except, logged, and the loop continues.

Usage:
    .venv/Scripts/python.exe -m backend.backfill --years 5
    .venv/Scripts/python.exe -m backend.backfill --lookback-days 1825
    .venv/Scripts/python.exe -m backend.backfill --markets KOSPI

Mirrors the fetch -> upsert shape of backend/store/ingest.py:
ensure_series_up_to_date, but forces the FULL deep lookback every time
instead of only fetching the gap since the last stored date — that's the
whole point of a backfill (existing rows may be sparse/short and need the
full window re-pulled, not just topped up).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime

from backend.store import db
from backend.store.series_map import build_registry
from config_loader import load_config, load_sectors

DEFAULT_LOOKBACK_DAYS = 1825  # 5 years
SKIP_PREFIX = "mcap:"  # point-in-time market caps, not historical series — not in
# build_registry's output today, but skip defensively if a future registry adds one.


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def backfill(markets=("KOSPI", "NASDAQ"), lookback_days=DEFAULT_LOOKBACK_DAYS, sectors_config=None):
    """Deepen series_daily history for every series in each market's registry.

    For each market: build the series_id -> (fetch_fn, source) registry, call
    fetch_fn(lookback_days) for every series_id, and upsert the returned points
    via db.upsert_series. One series' exception never aborts the run — it is
    caught, logged into the per-series result, and the loop continues.

    Returns a list of per-series result dicts:
        {"market": ..., "series_id": ..., "ok": bool, "rows": int, "error": str|None}
    """
    if sectors_config is None:
        sectors_config = load_sectors()

    db.init_db()

    results = []
    fetched_at = _now_iso()

    for market in markets:
        try:
            registry = build_registry(market, sectors_config)
        except Exception as exc:  # registry build itself must not abort other markets
            print(f"[{market}] FAILED to build registry: {exc}")
            results.append({
                "market": market, "series_id": None, "ok": False, "rows": 0, "error": str(exc),
            })
            continue

        for series_id, (fetch_fn, source) in registry.items():
            if series_id.startswith(SKIP_PREFIX):
                print(f"[{market}] {series_id}: skipped (point-in-time, not historical)")
                continue
            try:
                points = fetch_fn(lookback_days)
                rows = db.upsert_series(series_id, points, source=source, fetched_at=fetched_at)
                results.append({
                    "market": market, "series_id": series_id, "ok": True, "rows": rows, "error": None,
                })
                print(f"[{market}] {series_id}: OK ({rows} rows written)")
            except Exception as exc:  # noqa: BLE001 — one series must never abort the run
                results.append({
                    "market": market, "series_id": series_id, "ok": False, "rows": 0, "error": str(exc),
                })
                print(f"[{market}] {series_id}: FAILED ({exc})")

    return results


def _print_summary(results, lookback_days):
    total = len(results)
    succeeded = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]
    total_rows = sum(r["rows"] for r in succeeded)

    print("\n" + "=" * 70)
    print("BACKFILL SUMMARY")
    print("=" * 70)
    print(f"lookback_days requested: {lookback_days}")
    print(f"total series attempted:  {total}")
    print(f"succeeded:               {len(succeeded)}")
    print(f"failed:                  {len(failed)}")
    print(f"total rows written:      {total_rows}")

    if failed:
        print("\nFailures (expected for series needing network/auth not available here):")
        for r in failed:
            print(f"  [{r['market']}] {r['series_id']}: {r['error']}")

    # Per-series depth check: latest/earliest date + row count, straight from the DB
    # (post-backfill state), so the report reflects what's actually stored now.
    print("\nPer-series depth (post-backfill, from DB):")
    seen = set()
    for r in succeeded:
        key = (r["market"], r["series_id"])
        if key in seen:
            continue
        seen.add(key)
        pts = db.read_series(r["series_id"])
        if not pts:
            print(f"  [{r['market']}] {r['series_id']}: 0 rows in DB")
            continue
        earliest = pts[0][0]
        latest = pts[-1][0]
        print(f"  [{r['market']}] {r['series_id']}: {len(pts)} rows, {earliest} -> {latest}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="One-time idempotent historical backfill for series_daily.")
    parser.add_argument("--years", type=float, default=None, help="Lookback window in years (e.g. 5).")
    parser.add_argument("--lookback-days", type=int, default=None, help="Lookback window in days (overrides --years).")
    parser.add_argument("--markets", type=str, default=None, help="Comma-separated markets, e.g. KOSPI,NASDAQ.")
    args = parser.parse_args(argv)

    if args.lookback_days is not None:
        lookback_days = args.lookback_days
    elif args.years is not None:
        lookback_days = int(round(args.years * 365))
    else:
        lookback_days = DEFAULT_LOOKBACK_DAYS

    markets = tuple(m.strip() for m in args.markets.split(",")) if args.markets else ("KOSPI", "NASDAQ")

    print(f"Starting backfill: markets={markets}, lookback_days={lookback_days}")
    results = backfill(markets=markets, lookback_days=lookback_days)
    _print_summary(results, lookback_days)

    failed_count = sum(1 for r in results if not r["ok"])
    if failed_count == len(results) and results:
        # Total failure (e.g. no network at all) is worth a non-zero exit for scripting,
        # but partial failure is expected/normal and should not be treated as an error.
        sys.exit(1)


if __name__ == "__main__":
    main()
