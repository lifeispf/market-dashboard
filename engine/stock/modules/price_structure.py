"""engine/stock/modules/price_structure.py — §34 Price Structure.

정본: blueprint_micro/stock_engine/34_price_structure.md ("무엇을 살까가 아니라
언제 살까"). Price Layer, T0~T1 최중요, Strategy Engine과 직접 연결.

청사진 §34는 5개 하위축(Trend/Base/Breakout/Volatility/Risk·Reward)을 요구하지만,
현 close-only 시리즈로는 Trend(추세 방향)·Volatility(실현변동성)·장기 위치(200MA)만
계산 가능. Base/Breakout(거래량·신고가)·Risk·Reward(지지선)는 거래량·레벨 데이터가
필요 → 데이터 평면 이후 보강. 본 단계는 그 3개로 Composite State를 근사한다.

Composite State(§34 근사): Constructive/Neutral/Extended/Broken.
  - 추세 up + 200MA 위    -> Constructive (건전)
  - 추세 up + 200MA 아래  -> Neutral (회복 시도)
  - flat                  -> Neutral
  - 추세 down + 200MA 위  -> Extended (장기추세는 살아있으나 단기 둔화)
  - 추세 down + 200MA 아래 -> Broken (Veto 대상 — §34 "Structure=Broken -> Long 금지")
strength/confidence는 비검증 휴리스틱(§9.1).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from engine.core.contracts import ModuleOutput

if TYPE_CHECKING:
    from engine.core.context import Context
    from engine.stock.inputs import StockRow

_TREND_TRANSITION = {"up": "improving", "down": "weakening", "flat": "stable", None: None}


def _composite_state(trend_dir: str | None, above_ma200: bool | None) -> tuple[str | None, float | None]:
    if trend_dir is None:
        return None, None
    if trend_dir == "up":
        if above_ma200:
            return "Constructive", 0.8
        return "Neutral", 0.5
    if trend_dir == "flat":
        return "Neutral", 0.5
    # trend down
    if above_ma200:
        return "Extended", 0.4
    return "Broken", 0.15


class StockPriceStructureModule:
    """§34 — 종목의 가격 구조(추세·변동성·장기 위치) 관측."""

    id = "stock.price_structure"
    tier = "stock"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id: str, ctx: "Context") -> list[str]:
        return []

    def compute(self, entity_id: str, ctx: "Context", data: "StockRow") -> ModuleOutput:
        state, strength = _composite_state(data.trend_dir, data.above_ma200)
        if state is None:
            return ModuleOutput(
                module_id=self.id, state=None, transition=None, strength=None,
                confidence=None, narrative="가격 구조 데이터 없음(추세 산정 불가).",
                inputs={"trend_dir": data.trend_dir, "above_ma200": data.above_ma200,
                        "vol": data.vol, "approximation": "trend_ma_vol_only",
                        "price": data.price, "ma200": data.ma200, "low_20": data.low_20},
            )
        ma_txt = "200MA 위" if data.above_ma200 else ("200MA 아래" if data.above_ma200 is not None else "200MA 미상")
        narrative = f"{state} — 추세 {data.trend_dir}, {ma_txt}."
        return ModuleOutput(
            module_id=self.id, state=state, transition=_TREND_TRANSITION.get(data.trend_dir),
            strength=strength, confidence=None, narrative=narrative,
            inputs={"trend_dir": data.trend_dir, "above_ma200": data.above_ma200,
                    "vol": data.vol, "approximation": "trend_ma_vol_only",
                    "price": data.price, "ma200": data.ma200, "low_20": data.low_20},
        )
