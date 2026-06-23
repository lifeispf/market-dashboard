"""engine/sector/concentration.py — 시장 집중도 / 리더십 협소도 (Phase D-⑤).

근거: planning/elegant-soaring-twilight.md D-⑤. 섹터 시총·YTD가 한쪽으로
쏠려 있으면(예: 반도체 +158% YTD가 KOSPI 지수 상승을 견인) 지수 전체의
"건강한 상승"처럼 보이는 수치 뒤에 숨은 리스크가 있다. 이 모듈은 그 쏠림을
정량화한다 — fetch 없는 순수 함수(pure function), `gather_sector_inputs`가
만든 `SectorRow` 리스트(또는 동등한 dict 리스트: market_cap/marketCap,
ytd 키)를 입력으로 받는다.

## 공식

시총 비중(weight): `w_i = cap_i / sum(cap_j for j with cap_j is not None)`.
시총이 전부 None/누락이면 비중을 계산할 수 없어 전체가 None으로 degrade.

- **HHI** (Herfindahl-Hirschman Index): `sum(w_i ** 2)` — 0..1 스칼라.
  1.0에 가까울수록 단일 섹터 독점, 1/N에 가까울수록 균등분산.
- **effective_n**: `1 / HHI` — "체감 섹터 수". N개 섹터가 완전히 균등하면
  effective_n == N; 한 섹터가 지배하면 effective_n → 1.
- **top1_cap_pct / top3_cap_pct**: 시총 기준 상위 1개/3개 섹터가 전체 시총에서
  차지하는 비중(%, 0..100).
- **top1_ytd_contribution_pct / top3_ytd_contribution_pct**: 각 섹터의
  "지수 YTD 기여도"를 `contribution_i = w_i * ytd_i`로 근사(cap-weighted
  index의 1차 근사)하고, contribution이 양수(+)인 섹터들의 합을 분모로 하여
  상위 1개/3개 섹터가 그 양의 기여 합에서 차지하는 비중(%)을 구한다 — "상승을
  실제로 누가 견인했는가"를 드러내는 리더십 협소도 지표. cap 또는 ytd가
  None인 섹터는 기여도 계산에서 제외(skip)한다. 양의 기여 합이 0이면(전부
  하락 또는 데이터 없음) None.
- **leaders**: 시총 기준 상위 1~3개 섹터의 이름 리스트(표시용, 최대 3개).

모든 지표는 입력 부족 시 예외 없이 None으로 degrade한다(절대 raise하지 않음).
"""
from __future__ import annotations

from typing import Any, Sequence


def _get(row: Any, *names: str) -> Any:
    """SectorRow(속성) 또는 dict(camelCase/snake_case 키) 양쪽에서 값을 읽는다."""
    for name in names:
        if isinstance(row, dict):
            if name in row:
                return row[name]
        else:
            if hasattr(row, name):
                return getattr(row, name)
    return None


def _name(row: Any) -> str | None:
    return _get(row, "name")


def _cap(row: Any) -> float | None:
    return _get(row, "market_cap", "marketCap")


def _ytd(row: Any) -> float | None:
    return _get(row, "ytd")


def compute_concentration(rows: Sequence[Any]) -> dict[str, Any]:
    """섹터 행 리스트로부터 집중도/리더십 협소도 지표를 계산한다.

    Args:
        rows: `SectorRow` 객체 리스트 또는 동등한 dict 리스트(market_cap/
            marketCap, ytd, name 키 보유). 빈 리스트도 허용(전부 None).

    Returns:
        dict with keys: hhi, effective_n, top1_cap_pct, top3_cap_pct,
        top1_ytd_contribution_pct, top3_ytd_contribution_pct, leaders.
        데이터 부족 시 해당 필드는 None(leaders는 빈 리스트)으로 degrade한다.
        절대 raise하지 않는다.
    """
    result: dict[str, Any] = {
        "hhi": None,
        "effective_n": None,
        "top1_cap_pct": None,
        "top3_cap_pct": None,
        "top1_ytd_contribution_pct": None,
        "top3_ytd_contribution_pct": None,
        "leaders": [],
    }
    if not rows:
        return result

    caps: list[tuple[Any, float]] = []
    for row in rows:
        cap = _cap(row)
        if cap is None:
            continue
        try:
            cap_f = float(cap)
        except (TypeError, ValueError):
            continue
        if cap_f <= 0:
            continue
        caps.append((row, cap_f))

    total_cap = sum(c for _, c in caps)
    if not caps or total_cap <= 0:
        return result

    # weights, sorted descending by cap for top-N / leaders.
    weighted = [(row, cap, cap / total_cap) for row, cap in caps]
    weighted.sort(key=lambda t: t[2], reverse=True)

    hhi = sum(w ** 2 for _, _, w in weighted)
    result["hhi"] = hhi
    result["effective_n"] = (1.0 / hhi) if hhi > 0 else None

    top1_cap = weighted[0][1]
    top3_cap = sum(c for _, c, _ in weighted[:3])
    result["top1_cap_pct"] = (top1_cap / total_cap) * 100.0
    result["top3_cap_pct"] = (top3_cap / total_cap) * 100.0

    result["leaders"] = [
        n for n in (_name(row) for row, _, _ in weighted[:3]) if n is not None
    ]

    # YTD contribution = weight * ytd, computed only over rows with both
    # cap and ytd present (skip nulls). Ranked by contribution descending.
    contributions: list[tuple[Any, float]] = []
    for row, cap, w in weighted:
        ytd = _ytd(row)
        if ytd is None:
            continue
        try:
            ytd_f = float(ytd)
        except (TypeError, ValueError):
            continue
        contributions.append((row, w * ytd_f))

    positive_sum = sum(c for _, c in contributions if c > 0)
    if positive_sum > 0:
        contributions.sort(key=lambda t: t[1], reverse=True)
        top1_contrib = contributions[0][1] if contributions[0][1] > 0 else 0.0
        top3_contrib = sum(c for _, c in contributions[:3] if c > 0)
        result["top1_ytd_contribution_pct"] = (top1_contrib / positive_sum) * 100.0
        result["top3_ytd_contribution_pct"] = (top3_contrib / positive_sum) * 100.0

    return result
