"""engine/core/timeframes.py — timeframe bundle table + resample helpers.

Phase A (모니터링 대시보드 — 동적 타임프레임): `?tf=` 쿼리 파라미터가 RRG(섹터/종목)
와 가격 spark 추세를 어떤 "번들"(리샘플 해상도 + 윈도우)로 계산할지 결정한다.
정본: C:\\Users\\kenta\\.claude\\plans\\elegant-soaring-twilight.md.

CRITICAL INVARIANT: tf="1D"(또는 미지정)는 현재 동작과 byte-identical이어야 한다.
이를 보증하기 위해 1D는 resample=None(identity — 시리즈를 그대로 반환, 변환조차
하지 않음)이고, spark_n=60·rrg_window=10은 기존 하드코딩 상수/config["rrg"]와
동일하다. 이 파일은 PROTECTED 목록(config.json/scoring.py 등)에 없는 신규 파일이며,
보호 파일은 일절 수정하지 않는다.

pandas 버전: 이 환경은 2.3.3 — "ME"/"QE"/"YE"가 비-deprecated alias (구버전
"M"/"Q"/"A"는 2.2+에서 FutureWarning 대상이라 사용하지 않음).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_TF = "1D"


@dataclass(frozen=True)
class TimeframeBundle:
    """tf 하나에 대한 캔들 해상도 + 조회 기간 + RRG 윈도우 번들."""

    key: str
    label: str
    resample: str | None  # pandas resample rule, or None for identity (1D)
    spark_n: int
    rrg_window: int


TIMEFRAMES: dict[str, TimeframeBundle] = {
    "1D": TimeframeBundle(key="1D", label="일", resample=None, spark_n=60, rrg_window=10),
    "1W": TimeframeBundle(key="1W", label="주", resample="W-FRI", spark_n=60, rrg_window=10),
    "1M": TimeframeBundle(key="1M", label="월", resample="ME", spark_n=36, rrg_window=10),
    "1Q": TimeframeBundle(key="1Q", label="분기", resample="QE", spark_n=20, rrg_window=8),
    "1Y": TimeframeBundle(key="1Y", label="년", resample="YE", spark_n=10, rrg_window=4),
}


def normalize_tf(tf: Any) -> str:
    """None/모르는 값 -> "1D" (방어적 기본값). 알려진 키는 그대로 통과."""
    if tf in TIMEFRAMES:
        return tf
    return DEFAULT_TF


def resample_for_tf(series, tf: str):
    """series를 tf 번들의 resample rule로 리샘플한다 (`.resample(rule).last().dropna()`).

    tf="1D"(resample=None)는 IDENTITY — series를 변형 없이 그대로 반환한다. 이는
    byte-identical 불변식을 보증하기 위함이다: 어떤 추가 연산(copy 포함)도 부동소수점/
    dtype 동일성을 깨뜨릴 리스크가 있으므로 1D 경로는 입력을 손대지 않는다.

    series가 None이면 None을 그대로 반환한다(graceful degrade — 호출부의 길이 가드가
    이어서 처리한다).
    """
    if series is None:
        return None
    bundle = TIMEFRAMES[normalize_tf(tf)]
    if bundle.resample is None:
        return series
    return series.resample(bundle.resample).last().dropna()


def rrg_window_for(tf: str) -> int:
    return TIMEFRAMES[normalize_tf(tf)].rrg_window


def spark_n_for(tf: str) -> int:
    return TIMEFRAMES[normalize_tf(tf)].spark_n


_LOOKBACK_DAYS = {"1D": 400, "1W": 600, "1M": 1300, "1Q": 2200, "1Y": 4000}


def lookback_days_for(tf: str) -> int:
    """tf별 시리즈 조회기간(일). Phase D-⑥: backfill로 깊어진 series_daily(~1825행)를
    1M/1Q/1Y가 실제로 읽을 수 있도록 tf가 길수록 더 깊이 읽는다. tf="1D"는 400으로
    기존과 동일 -- byte-identical 불변식 보증."""
    return _LOOKBACK_DAYS.get(normalize_tf(tf), 400)
