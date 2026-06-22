"""GET /api/stocks/{market} — Stock tier read endpoint (Stage 5).

00_architecture.md §7.1: tier별 리소스, 전부 동일 envelope(EngineOutput).
sectors.json의 key/star 종목(레거시 `leaders` 대상)에 Price 레이어 해석(Verdict)을
얹어 노출한다. 종목 콘텐츠(role/thesis/risk)는 기존 동결 payload의 `leaders`가 계속
제공 — 본 엔드포인트는 정량 판정(direction/lead_pattern/position_size_hint + §35/§34
모듈)만 담당한다(고도 분리: 01_altitude_separation.md).

캐스케이드(sector→stock context)는 /api/briefing(추후)이 담당. 본 엔드포인트는
종목을 단독(Context.root) 실행한다.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engine.core.timeframes import normalize_tf
from engine.stock.engine import run_stocks

router = APIRouter()

VALID_MARKETS = ("KOSPI", "NASDAQ")


@router.get("/api/stocks/{market}")
def get_stocks(market: str, tf: str = "1D"):
    market = market.upper()
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=404, detail=f"unknown market: {market}")
    tf = normalize_tf(tf)
    try:
        outputs = run_stocks(market, tf=tf)
    except Exception as exc:  # never 500 — graceful degradation(§9.3)
        raise HTTPException(status_code=503, detail=f"stock assembly failed: {exc}")
    return {
        "tier": "stock",
        "market": market,
        "stocks": [eo.to_dict() for eo in outputs],
    }
