"""engine/stock/action.py — 투명 룰 기반 실행 레벨(진입/손절/비중).

⚠️ **투자자문 아님.** 차팅 플랫폼의 손절·포지션 계산기처럼 **공개된 규칙**으로 레벨을
산출할 뿐이며, walk-forward 검증 전이라 비검증 휴리스틱(§9.1)이다. 개인화 매매 추천이
아니다 — 프론트는 항상 디스클레이머와 함께 표시한다.

규칙(전부 측정값에서 결정적 — 감사·테스트 가능):
  - 진입: 구조 상태 조건부(Constructive/Neutral=현재가 구간, Extended=되돌림 대기,
    Broken/avoid=보류).
  - 손절: 구조적(MA200 위면 MA200, 아니면 최근 20일 저점)과 변동성(10거래일 실현변동성
    ×1.5) 중 가장 가까운(보수적) 쪽.
  - 비중: 변동성 타게팅(목표 연 15% / 종목 실현변동성, 최대 20%) × size_hint 배수.
"""
from __future__ import annotations

import math
from typing import Any

_HINT_FACTOR = {"full": 1.0, "half": 0.5, "quarter": 0.25, "avoid": 0.0}
_TARGET_VOL = 15.0  # 목표 포트폴리오 연환산 변동성(%)
_MAX_WEIGHT = 20.0  # 단일 종목 최대 비중(%)


def _fmt(v: float) -> str:
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.2f}"


def build_action_levels(
    price: float | None,
    ma200: float | None,
    low_20: float | None,
    vol_annual_pct: float | None,
    above_ma200: bool | None,
    struct_state: str | None,
    size_hint: str | None,
) -> dict[str, Any] | None:
    """투명 룰 실행 레벨. 데이터 부족 시 None(절대 raise 안 함)."""
    if price is None or price <= 0 or vol_annual_pct is None or vol_annual_pct <= 0:
        return None

    # ---- 손절: 구조 후보 + 변동성 후보 중 가장 가까운(보수적) 쪽 ----
    vol_stop = price * (1 - (vol_annual_pct * math.sqrt(10.0 / 252.0) * 1.5) / 100.0)
    candidates: list[tuple[float, str]] = []
    if above_ma200 and ma200 is not None and ma200 < price:
        candidates.append((ma200, "구조(MA200)"))
    if low_20 is not None and low_20 < price:
        candidates.append((low_20, "구조(최근 20일 저점)"))
    candidates.append((vol_stop, "변동성(10일 실현변동성×1.5)"))
    valid = [(lv, r) for lv, r in candidates if lv is not None and 0 < lv < price]
    stop, stop_rule = (max(valid, key=lambda x: x[0]) if valid else (None, None))
    stop_pct = (stop / price - 1) * 100 if stop is not None else None

    # ---- 비중: 변동성 타게팅 × size_hint 배수 ----
    hint = _HINT_FACTOR.get(size_hint or "", 0.5)
    raw_w = min(_MAX_WEIGHT, _TARGET_VOL / vol_annual_pct * 100.0)
    weight_pct = round(raw_w * hint, 1)

    # ---- 진입: 구조 조건부 ----
    if size_hint == "avoid" or struct_state == "Broken":
        entry = "진입 보류 — 구조 미흡(회피)"
    elif struct_state == "Extended":
        entry = "되돌림 대기 — 추격 비권장"
    else:
        entry = f"구조 양호 시 현재가({_fmt(price)}) 부근 진입 구간"

    return {
        "entry": entry,
        "stop": round(stop, 2) if stop is not None else None,
        "stop_pct": round(stop_pct, 1) if stop_pct is not None else None,
        "stop_rule": stop_rule,
        "weight_pct": weight_pct,
        "weight_rule": f"변동성 타게팅(목표 {_TARGET_VOL:.0f}% / 종목 {vol_annual_pct:.0f}%) × 사이즈 {size_hint}",
        "disclaimer": "기계적 룰 산출 · 투자자문 아님 · 비검증(walk-forward 전)",
    }
