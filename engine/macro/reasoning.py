"""engine/macro/reasoning.py — 룰베이스 추론 콘텐츠 생성(Why / Supports / Counter-Evidence / Invalidation).

macro Verdict의 narrative(왜)·risks(반대근거)·supports(찬성근거)·invalidation(무효화
조건)을 **측정 팩터에서 규칙적으로** 만든다. LLM 없음 — 결정적·감사가능·단위테스트 가능.

설계 원칙(00_architecture.md §1.1, 이 프로젝트의 정직성 기조):
  - 측정값 조건이 충족될 때만 각 항목을 발화한다(근거 없는 단정·환각 인과 금지).
  - 상관≠인과: "견인/발목"은 동행 관측 서술이지 검증된 인과가 아니다(검증은 스코어카드).
  - 동결 MarketPayload·등가성 게이트와 무관: MacroRulebook이 채우는 Verdict.narrative/
    risks/invalidation/extra["reasoning"]은 legacy 어댑터가 읽지 않는다(envelope 전용).

입력은 engine/macro/inputs.py:MacroInputs(이미 gather된 측정값) 하나뿐 — fetch 없음.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.macro.inputs import MacroInputs

# S01~S06 사람이 읽는 라벨(00_architecture.md §5). score 0~100: 높을수록 유동성 우호.
_FACTOR_LABEL = {
    "S01": "중앙은행",
    "S02": "외국인 수급",
    "S03": "국내 신용",
    "S04": "美 유동성",
    "S05": "원화 환율",
    "S06": "글로벌 크레딧",
}

# 표시용 분류 임계(점수 자체는 scoring.py 소관 — 여기선 서술 분류만). 50 중립 기준 ±10.
_SUPPORT_HI = 60.0  # 이상이면 '견인'
_DRAG_LO = 40.0  # 이하면 '발목'

_REGIME_WORD = {
    "bull": "BULL 도달 가능(재평가 연료 부분충전)",
    "hyper": "HYPER 연료 존재(지속가능성은 별도 경고)",
    "base": "BASE 한계(멀티플 유지선)",
}


def _classify(score: float | None) -> str | None:
    if score is None:
        return None  # 미가용 — 서술에서 제외(임의값 금지)
    if score >= _SUPPORT_HI:
        return "support"
    if score <= _DRAG_LO:
        return "drag"
    return "neutral"


def build_macro_reasoning(inputs: "MacroInputs") -> dict[str, Any]:
    """MacroInputs → {narrative, supports, risks, invalidation}. 절대 raise하지 않는다."""
    subs = inputs.subscores or {}
    weights = inputs.weights or {}
    regime = inputs.regime

    supports_f: list[str] = []
    drags_f: list[str] = []
    for sid, label in _FACTOR_LABEL.items():
        if weights.get(sid, 0) <= 0:
            continue  # 이 시장 가중치 0 — 무관 팩터(예: NASDAQ의 원화 환율)는 서술에서 제외
        cls = _classify(subs.get(sid))
        if cls == "support":
            supports_f.append(label)
        elif cls == "drag":
            drags_f.append(label)

    # ---- narrative(Why): regime을 구성 팩터로 풀어쓴다 ----
    parts = [f"유동성 {_REGIME_WORD.get(regime, '산정 불가')}"]
    if supports_f:
        parts.append("견인: " + "·".join(supports_f))
    if drags_f:
        parts.append("발목: " + "·".join(drags_f))
    narrative = " / ".join(parts)

    # ---- 공통 측정값 ----
    up_ratio = inputs.up_ratio
    pos = inputs.position or {}
    fg = inputs.fear_greed or {}
    fg_score = fg.get("score")

    # ---- supports(찬성근거, Debate 양면) ----
    supports: list[str] = [f"{s} 우호" for s in supports_f]
    if up_ratio is not None and up_ratio >= 0.58:
        supports.append(f"breadth 양호(상승 {round(up_ratio * 100)}%)")
    if fg_score is not None and fg_score <= 25:
        supports.append(f"심리 극단공포(F&G {round(fg_score)}) — 역발상 반등 여지")
    if pos.get("band") == "base" and regime in ("bull", "hyper"):
        supports.append("밸류 여유(천장 대비 하단)")

    # ---- risks(반대근거/Counter-Evidence) — 측정 조건 충족 시에만 ----
    risks: list[str] = [f"{d} 부진" for d in drags_f]
    if up_ratio is not None and up_ratio < 0.45:
        risks.append(f"breadth 약화(상승 {round(up_ratio * 100)}%) — 폭 좁은 상승")
    if pos.get("band") == "hyper":
        risks.append("밸류 부담(HYPER 밴드 — 멀티플 과열)")
    elif pos.get("distance_pct") is not None and 0 <= pos["distance_pct"] < 5:
        # 양(+)의 소폭 여력만 '근접'. 음수(천장 초과)는 아래 recon 과열 risk가 담당.
        risks.append(f"천장 근접(여력 {pos['distance_pct']:+.0f}%)")
    if fg_score is not None and fg_score >= 75:
        risks.append(f"심리 과열(F&G {round(fg_score)})")
    if inputs.recon == "overheated":
        risks.append("가격-유동성 괴리(과열 — 천장 초과)")

    # ---- invalidation(무효화 조건) ----
    invalidation: list[str] = []
    if regime in ("bull", "hyper"):
        invalidation.append("regime BASE 강등 시 무효")
    if inputs.usdkrw is not None:
        invalidation.append("원화 추가 약세(환율 게이트 상향 돌파) 시")
    invalidation.append("breadth 약세 지속(폭 Lv≤2) 시 추세 신뢰도 하락")

    return {
        "narrative": narrative,
        "supports": supports,
        "risks": risks,
        "invalidation": invalidation,
    }


# ---- Layer 0 Executive Summary (5초 시장 진단) -------------------------------
# 캐스케이드(macro verdict + 섹터)에서 룰베이스로 합성. 시장상태/내부체력/상승여력/현재전략
# 4줄 + 한 줄 헤드라인. 전부 측정 verdict에서 도출 — 새 예측·LLM 없음.

_DIRECTION_STATE = {
    "strong_up": ("강한 상승 추세", "up"),
    "up": ("상승 추세 유지", "up"),
    "neutral": ("중립·방향성 약함", "flat"),
    "down": ("하락 압력", "down"),
    "strong_down": ("강한 하락 추세", "down"),
}


def build_executive_summary(macro: Any, sectors: Any = None) -> dict[str, Any]:
    """macro EngineOutput(+섹터 리스트)에서 Layer0 요약을 만든다. 절대 raise 안 함."""
    v = getattr(macro, "verdict", None)
    if v is None:
        return {"headline": "산정 불가", "lines": []}
    ex = v.extra or {}
    risks = v.risks or []
    supports = ex.get("supports") or []
    regime = ex.get("regime")
    composite = ex.get("composite")
    recon = ex.get("reconciliation")
    pos = ex.get("position") or {}

    breadth_weak = any("breadth 약화" in r for r in risks)
    breadth_ok = any("breadth 양호" in s for s in supports)
    overheated = recon == "overheated" or pos.get("band") == "hyper"

    # 1) 시장 상태(State)
    state_txt, state_tone = _DIRECTION_STATE.get(v.direction, ("산정 불가", "flat"))
    if overheated:
        state_txt += " · 과열"

    # 2) 내부 체력(Health) — breadth/참여
    if breadth_weak:
        health = ("약화 (상승 폭 좁음)", "down")
    elif breadth_ok:
        health = ("양호 (폭넓은 참여)", "up")
    else:
        health = ("보통", "flat")

    # 3) 상승 여력(Potential) — regime/composite, 과열이면 소진
    comp_txt = f"composite {round(composite)}" if composite is not None else "산정 불가"
    if overheated:
        potential = (f"제한적 (과열·{comp_txt})", "down")
    elif regime == "bull":
        potential = (f"중립~여유 ({comp_txt})", "flat")
    elif regime == "hyper":
        potential = (f"존재하나 과열 경고 ({comp_txt})", "flat")
    elif regime == "base":
        potential = (f"낮음 ({comp_txt})", "down")
    else:
        potential = (comp_txt, "flat")

    # 4) 현재 전략(Strategy) — 룰 조합
    if overheated:
        strategy = ("리스크 관리 · 추격매수 자제", "down")
    elif breadth_weak:
        strategy = ("주도주 선별 (폭 좁아 지수추종 부담)", "flat")
    elif v.direction in ("up", "strong_up") and breadth_ok:
        strategy = ("추세 추종 · 주도주 비중", "up")
    else:
        strategy = ("관망 · 신호 대기", "flat")

    # 주도 섹터 한 줄(있으면)
    lead_name = None
    for s in sectors or []:
        sv = getattr(s, "verdict", None)
        if sv and sv.lead_pattern == "leading":
            lead_name = getattr(s, "entity_id", None)
            break

    lines = [
        {"label": "시장 상태", "value": state_txt, "tone": state_tone},
        {"label": "내부 체력", "value": health[0], "tone": health[1]},
        {"label": "상승 여력", "value": potential[0], "tone": potential[1]},
        {"label": "현재 전략", "value": strategy[0], "tone": strategy[1]},
    ]
    headline = f"{state_txt} · 체력 {health[0].split()[0]} · 여력 {potential[0].split()[0]} → {strategy[0]}"
    return {"headline": headline, "lines": lines, "lead_sector": lead_name}

