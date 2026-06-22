"""engine/macro/modules/_common.py — shared mapping helpers for S01-S06 modules.

These mappings are copied verbatim from backend/api/market.py's pre-retrofit
`_assemble_live` (the headroom-word / direction-word logic in its "Sources
block"). They are extracted here so every S0X module applies the exact same
state/transition vocabulary instead of re-deriving it slightly differently.
"""
from __future__ import annotations

# headroom band label: score>=60 "high", >=35 "mid", else "low"; None stays None.
def headroom_state(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 60:
        return "high"
    if score >= 35:
        return "mid"
    return "low"


# raw up/down/flat direction -> Transition vocabulary (engine.core.contracts.Transition).
_TRANSITION_MAP = {"up": "improving", "down": "weakening", "flat": "stable", None: None}


def to_transition(raw_dir: str | None) -> str | None:
    return _TRANSITION_MAP.get(raw_dir, None)


# Mirrors market.py's pre-retrofit headroom_word (used inside dirLabel) so module
# narratives read identically to the frozen sources[].dirLabel text.
def headroom_word(score: float | None) -> str:
    if score is None:
        return "데이터 부족"
    if score >= 60:
        return "여력 높음"
    if score >= 35:
        return "여력 중간"
    return "여력 낮음"


DIR_WORD = {"up": "상승", "down": "하락", "flat": "보합", None: "추세 불명"}
