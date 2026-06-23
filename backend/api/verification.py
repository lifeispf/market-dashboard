"""GET /api/verification/{market} — Phase F 검증 스코어카드 엔드포인트.

engine/verification/scorecard.build_scorecard를 감싸 노출한다. 백테스트 가능
부분집합(F&G 극단·섹터 RRG hit-rate·모멘텀 IC·FRED-regime 팩터 IC)의 실측
신뢰도를 대시보드 "신호 신뢰도" 패널에 공급한다. 절대 500을 내지 않는다 —
실패 시 limitation note만 담은 빈 스코어카드로 degrade(§9.3).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from engine.verification.scorecard import build_scorecard

router = APIRouter()

VALID_MARKETS = ("KOSPI", "NASDAQ")


@router.get("/api/verification/{market}")
def get_verification(market: str):
    market = market.upper()
    if market not in VALID_MARKETS:
        raise HTTPException(status_code=404, detail=f"unknown market: {market}")
    try:
        scorecard = build_scorecard(market)
    except Exception as exc:  # never 500 — degrade gracefully
        scorecard = {"limitations": f"스코어카드 산정 실패: {exc}", "index_sample_n": 0}
    return {"tier": "verification", "market": market, "scorecard": scorecard}
