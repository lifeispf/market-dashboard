"""scripts/generate_payloads.py — Cloudflare 무료 배포용 payload 생성기.

planning/elegant-soaring-twilight.md(Cloudflare 배포) Phase 2. 기존 FastAPI 라우트
함수를 in-process로 직접 호출해(추가 의존성 없음 — httpx/TestClient 불필요) 모든
(endpoint × market × tf) 응답을 받아 Cloudflare KV `bulk put` 포맷의 단일 파일
(kv_payloads.json)로 직렬화한다.

- 라우트 함수(get_market 등)는 평범한 dict를 반환하므로 라이브 `/api/*` 응답과
  동일하다(동일 코드 경로). 키는 Worker의 URL→KV키 매핑 스킴과 정확히 일치.
- 출력: [{"key","value"}] 배열(value=응답 JSON 문자열) → `wrangler kv bulk put`.
- 보호 파일 무수정: 엔진/라우트를 호출만 한다.

실행:
    .venv/Scripts/python.exe scripts/generate_payloads.py [--out kv_payloads.json]

GitHub Action: 같은 명령 후 `wrangler kv bulk put kv_payloads.json
--namespace-id <id> --remote`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Make the repo root importable (so `backend`/`engine` resolve) regardless of CWD —
# this script lives in scripts/ which would otherwise be the only path entry.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MARKETS = ("KOSPI", "NASDAQ")
TFS = ("1D", "1W", "1M", "1Q", "1Y")


def build_entries() -> list[dict]:
    """라우트 함수를 직접 호출해 [{"key","value"}] 항목을 만든다. key는 Worker가
    URL→KV키로 매핑하는 스킴(market:{m}:{tf} 등)과 정확히 일치한다."""
    from backend.api.history import get_history
    from backend.api.market import get_market
    from backend.api.sectors import get_sectors
    from backend.api.stocks import get_stocks
    from backend.api.verification import get_verification
    from backend.api.health import health

    entries: list[dict] = []
    failures: list[str] = []

    def add(key: str, fn):
        t0 = time.time()
        try:
            payload = fn()
            entries.append({"key": key, "value": json.dumps(payload, ensure_ascii=False)})
            print(f"  + {key:24s} ({time.time() - t0:.1f}s)")
        except Exception as exc:  # never abort the whole run on one endpoint
            failures.append(f"{key} -> {exc}")
            print(f"  ! {key:24s} {exc}", file=sys.stderr)

    for m in MARKETS:
        for tf in TFS:
            add(f"market:{m}:{tf}", lambda m=m, tf=tf: get_market(m, tf))
            add(f"sectors:{m}:{tf}", lambda m=m, tf=tf: get_sectors(m, tf))
            add(f"stocks:{m}:{tf}", lambda m=m, tf=tf: get_stocks(m, tf))
            add(f"history:{m}:{tf}", lambda m=m, tf=tf: get_history(m, tf))
        add(f"verification:{m}", lambda m=m: get_verification(m))
    add("health", lambda: health())

    if failures:
        print(f"\n{len(failures)} endpoint(s) failed:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate Cloudflare KV bulk payloads from the FastAPI route functions.")
    parser.add_argument("--out", default="kv_payloads.json", help="Output bulk JSON path.")
    args = parser.parse_args(argv)

    print(f"Generating payloads ({len(MARKETS)} markets x {len(TFS)} tf + verification + health)...")
    entries = build_entries()

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)

    total_bytes = sum(len(e["value"]) for e in entries)
    print(f"\nWrote {len(entries)} keys to {args.out} ({total_bytes / 1024:.0f} KB total).")
    if not entries:
        sys.exit(1)


if __name__ == "__main__":
    main()
