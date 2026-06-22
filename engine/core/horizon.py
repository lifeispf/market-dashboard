"""engine/core/horizon.py — 전 tier 단일 정규 Horizon enum.

정본: planning/blueprint_unified/00_architecture.md §9.2.

macro 분석(`macro Ideation/blueprint_v3.md` §15)과 micro 분석
(`blueprint_micro/00_index.md` §5, `30_stock_engine`)이 "같은 단어, 다른 기간"으로
Horizon을 정의해 왔다. 이 모듈은 그 불일치를 해소하는 단일 정규 enum과,
macro의 레거시 호라이즌 어휘를 정규 enum으로 매핑하는 헬퍼를 제공한다.

정규 경계값 (00_architecture.md §9.2 잠정안 — micro 기준 채택, macro를 매핑):
    T0 = 1~5 거래일   (초단기 — 며칠 내 전개)
    T1 = 1~6 주        (단기 — 한 분기 이내 회전)
    T2 = 1~6 개월      (중기 — 사이클 한 구간)
    T3 = 1~2 년        (장기 — 레짐/구조적 변화)

macro 레거시 호라이즌 (`macro Ideation/blueprint_v3.md` §15):
    macro "T1" = 1~5일   -> 정규 "T0" (1~5거래일과 기간이 거의 일치)
    macro "T2" = 1~4주   -> 정규 "T1" (1~6주에 포함되는 단기 구간)

위 매핑은 00_architecture.md §9.2가 명시한 결정("macro 모듈은 매핑 테이블로
흡수")을 코드로 구현한 것이다. macro에는 정규 T2/T3에 대응하는 레거시 어휘가
없으므로(§15는 T1/T2까지만 정의) 그 두 값은 매핑 대상에서 제외한다 — 필요해지면
이 헬퍼를 확장한다.
"""

from __future__ import annotations

from typing import Literal

Horizon = Literal["T0", "T1", "T2", "T3"]
"""전 tier 공용 정규 Horizon. 모듈 docstring 상단의 경계값 표를 정본으로 한다."""

# macro 레거시 호라이즌 라벨 -> 정규 Horizon 매핑 테이블.
# 키는 macro가 실제로 사용하는 레거시 식별자("T1"/"T2")이며, 정규 Horizon의
# 동일 라벨("T0"/"T1")과는 의미가 다르므로 혼동 방지를 위해 이 모듈 밖으로
# 레거시 라벨을 그대로 노출하지 않는다(map_macro_horizon을 통해서만 변환).
_MACRO_LEGACY_TO_REGULAR: dict[str, Horizon] = {
    "T1": "T0",  # macro T1 = 1~5일
    "T2": "T1",  # macro T2 = 1~4주
}


def map_macro_horizon(legacy: str) -> Horizon:
    """macro 레거시 호라이즌 라벨을 정규 Horizon enum 값으로 매핑한다.

    Args:
        legacy: macro `blueprint_v3.md` §15의 레거시 라벨("T1" 또는 "T2").
            "T1"은 1~5일(정규 T0에 흡수), "T2"는 1~4주(정규 T1에 흡수).

    Returns:
        정규 Horizon 값("T0" 또는 "T1").

    Raises:
        ValueError: legacy가 알려진 macro 레거시 라벨이 아닐 때. macro §15는
            T1/T2까지만 정의하므로 그 외 값(정규 T2/T3 포함)은 의도적으로
            거부한다 — 우아한 degrade 원칙(§9.3)에 따라 임의로 추정값을
            반환하지 않는다.
    """
    try:
        return _MACRO_LEGACY_TO_REGULAR[legacy]
    except KeyError as exc:
        raise ValueError(
            f"알 수 없는 macro 레거시 호라이즌: {legacy!r}. "
            f"알려진 값: {sorted(_MACRO_LEGACY_TO_REGULAR)}"
        ) from exc
