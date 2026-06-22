"""engine/sector/classification.py — 섹터 위험선호 성격(경기민감도) 정적 분류.

§21 상대강도(동적 신호)와 직교하는 정적 속성. 공격(고베타·경기민감)/중립/
방어(저베타) 3분류로, 프론트가 좌/중/우 열로 배치하고 열 내부는 현재 방향·강도로
정렬한다. sectors.json(보호 파일)을 건드리지 않기 위해 분류는 엔진단 상수로 둔다.
"""
from __future__ import annotations

from typing import Literal

RiskProfile = Literal["offensive", "neutral", "defensive"]

# 코드 → 위험선호 성격. KOSPI(소문자 코드)·NASDAQ(대문자 코드) 코드가 서로 겹치지
# 않으므로 단일 dict로 충분하다. (기본값: 분류 미정의 코드는 "neutral".)
SECTOR_RISK_PROFILE: dict[str, RiskProfile] = {
    # --- KOSPI ---
    "semi": "offensive", "chem": "offensive", "ship": "offensive",
    "auto": "offensive", "sec": "offensive",
    "power": "neutral", "bank": "neutral", "bio": "neutral",
    "telco": "defensive", "cons": "defensive",
    # --- NASDAQ ---
    "Tech": "offensive", "ConsDisc": "offensive", "Comm": "offensive",
    "Mat": "offensive", "Energy": "offensive",
    "Fin": "neutral", "Indus": "neutral", "RE": "neutral",
    "Staples": "defensive", "Util": "defensive", "Health": "defensive",
}


def classify(code: str) -> RiskProfile:
    """섹터 코드의 위험선호 성격을 반환. 미정의 코드는 중립으로 우아하게 degrade."""
    return SECTOR_RISK_PROFILE.get(code, "neutral")
