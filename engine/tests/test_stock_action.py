"""engine/tests/test_stock_action.py — 투명 룰 실행 레벨(engine/stock/action.py) 단위테스트.

룰이 결정적이라 고정 입력으로 검증. 안전성(회피/디스클레이머)도 테스트한다.
"""
from __future__ import annotations

import unittest

from engine.stock.action import build_action_levels


class StockActionTests(unittest.TestCase):
    def test_none_on_missing_data(self):
        self.assertIsNone(build_action_levels(None, None, None, 40, True, "Constructive", "full"))
        self.assertIsNone(build_action_levels(100, 90, 95, None, True, "Constructive", "full"))

    def test_stop_is_below_price_and_conservative(self):
        a = build_action_levels(price=100, ma200=90, low_20=95, vol_annual_pct=40,
                                above_ma200=True, struct_state="Constructive", size_hint="full")
        self.assertIsNotNone(a)
        self.assertLess(a["stop"], 100)
        self.assertLessEqual(a["stop_pct"], 0)
        # 가장 가까운(보수적) 손절 — 후보(MA200=90·저점=95·변동성≈88) 중 95 선택.
        self.assertEqual(a["stop"], 95)

    def test_avoid_blocks_entry_and_zero_weight(self):
        a = build_action_levels(100, 90, 95, 40, True, "Broken", "avoid")
        self.assertIn("보류", a["entry"])
        self.assertEqual(a["weight_pct"], 0.0)

    def test_extended_waits_for_pullback(self):
        a = build_action_levels(100, 90, 95, 40, True, "Extended", "quarter")
        self.assertIn("되돌림", a["entry"])

    def test_weight_scales_with_size_hint(self):
        full = build_action_levels(100, 90, 95, 40, True, "Constructive", "full")["weight_pct"]
        quarter = build_action_levels(100, 90, 95, 40, True, "Constructive", "quarter")["weight_pct"]
        self.assertGreater(full, quarter)

    def test_lower_vol_gets_higher_weight(self):
        lowvol = build_action_levels(100, 90, 95, 15, True, "Constructive", "full")["weight_pct"]
        highvol = build_action_levels(100, 90, 95, 60, True, "Constructive", "full")["weight_pct"]
        self.assertGreaterEqual(lowvol, highvol)

    def test_disclaimer_is_present(self):
        a = build_action_levels(100, 90, 95, 40, True, "Constructive", "full")
        self.assertIn("투자자문 아님", a["disclaimer"])


if __name__ == "__main__":
    unittest.main()
