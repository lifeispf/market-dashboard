"""GET /api/sectors/{market} — Sector tier read endpoint (Stage 4).

00_architecture.md §7.1: tier별 리소스, 전부 동일 envelope(EngineOutput).
프론트(아직 미배선)는 이 엔드포인트로 섹터별 Verdict(direction/strength/
lead_pattern + §21 모듈 카드)를 소비한다. 기존 GET /api/market/{market}의
동결 `sectors[]`(metric만)는 그대로 유지되며, 이 엔드포인트는 그 위에 해석
레이어(Verdict)를 더해 노출한다 — 둘은 같은 RRG 원시값을 본다.

캐스케이드(macro→sector context)는 /api/briefing(추후)이 담당한다. 본
엔드포인트는 섹터를 단독(Context.root) 실행한다 — macro 재fetch 비용 회피.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engine.sector.engine import run_sectors

router = APIRouter()

VALID_MARKETS = ("KOSPI", "NASDAQ")


@router.get("/api/sectors/{market}")
def get_sectors(market: str):
    market = market.upper()
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=404, detail=f"unknown market: {market}")
    try:
        outputs = run_sectors(market)
    except Exception as exc:  # never 500 — graceful degradation(§9.3)
        raise HTTPException(status_code=503, detail=f"sector assembly failed: {exc}")
    return {
        "tier": "sector",
        "market": market,
        "sectors": [eo.to_dict() for eo in outputs],
    }
