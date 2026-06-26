"""GET /api/briefing/{market} — full cascade (Stage 5+, §7.1).

Macro → Sector → Stock을 context 전파로 한 번에 실행해(engine/cascade.py) 세 tier의
EngineOutput을 한 응답으로 반환한다. 프론트의 ContextRail(§8.2 "통일 플로우의 UX
본체")과 랜딩 드릴다운이 이걸 소비한다.

단독 tier 엔드포인트(/api/sectors·/api/stocks)와 달리, 여기서는 하위 tier가 상위
verdict를 context로 받는다 — stock의 context.upstream에 macro+sector가 들어있고,
소속 섹터가 약세면 종목 verdict가 강등된다(§39 §5).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engine.cascade import run_cascade
from engine.macro.reasoning import build_executive_summary

router = APIRouter()

VALID_MARKETS = ("KOSPI", "NASDAQ")


@router.get("/api/briefing/{market}")
def get_briefing(market: str):
    market = market.upper()
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=404, detail=f"unknown market: {market}")
    try:
        cascade = run_cascade(market)
    except Exception as exc:  # never 500 — graceful degradation(§9.3)
        raise HTTPException(status_code=503, detail=f"briefing assembly failed: {exc}")
    # Layer0 Executive Summary(룰베이스 합성) — 가산이라 실패해도 캐스케이드는 반환.
    try:
        summary = build_executive_summary(cascade.macro, cascade.sectors)
    except Exception:
        summary = {"headline": "산정 불가", "lines": []}
    return {"tier": "briefing", "summary": summary, **cascade.to_dict()}
