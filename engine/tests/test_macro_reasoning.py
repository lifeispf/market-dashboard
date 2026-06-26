"""engine/tests/test_macro_reasoning.py — 룰베이스 추론(engine/macro/reasoning.py) 단위테스트.

build_macro_reasoning은 측정 팩터→문장 규칙이라 결정적이다. stdlib unittest(venv에 pytest
미설치, 기존 컨벤션). MacroInputs 전체를 만들 필요 없이 build_macro_reasoning이 읽는
필드만 가진 가벼운 stub(SimpleNamespace)로 규칙을 검증한다.
"""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from engine.macro.reasoning import build_macro_reasoning


def _inputs(**kw):
    base = dict(
        subscores={}, weights={"S01": 1, "S02": 1, "S03": 1, "S04": 1, "S05": 1, "S06": 1},
        regime="bull", up_ratio=None, position={}, fear_greed={}, recon=None, usdkrw=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


class MacroReasoningTests(unittest.TestCase):
    def test_never_raises_on_empty(self):
        r = build_macro_reasoning(_inputs(subscores={}, weights={}, regime=None))
        for key in ("narrative", "supports", "risks", "invalidation"):
            self.assertIn(key, r)
        self.assertIsInstance(r["narrative"], str)

    def test_support_and_drag_classification(self):
        r = build_macro_reasoning(_inputs(subscores={"S06": 80, "S05": 20, "S01": 50}))
        self.assertIn("견인: 글로벌 크레딧", r["narrative"])
        self.assertIn("발목: 원화 환율", r["narrative"])
        # 중립(50)인 S01은 견인/발목 어디에도 안 들어간다.
        self.assertNotIn("중앙은행", r["narrative"])
        self.assertIn("원화 환율 부진", r["risks"])

    def test_zero_weight_factor_excluded(self):
        # S05 가중치 0 → 점수가 낮아도 '발목'/risks에 안 나온다(시장 무관 팩터).
        r = build_macro_reasoning(
            _inputs(subscores={"S05": 10}, weights={"S05": 0, "S06": 1})
        )
        self.assertNotIn("원화 환율", r["narrative"])
        self.assertNotIn("원화 환율 부진", r["risks"])

    def test_breadth_weak_is_risk_strong_is_support(self):
        weak = build_macro_reasoning(_inputs(up_ratio=0.33))
        self.assertTrue(any("breadth 약화" in x for x in weak["risks"]))
        strong = build_macro_reasoning(_inputs(up_ratio=0.64))
        self.assertTrue(any("breadth 양호" in x for x in strong["supports"]))

    def test_hyper_band_and_fg_overheat_are_risks(self):
        r = build_macro_reasoning(_inputs(position={"band": "hyper"}, fear_greed={"score": 82}))
        self.assertTrue(any("밸류 부담" in x for x in r["risks"]))
        self.assertTrue(any("심리 과열" in x for x in r["risks"]))

    def test_extreme_fear_is_contrarian_support(self):
        r = build_macro_reasoning(_inputs(fear_greed={"score": 18}))
        self.assertTrue(any("극단공포" in x for x in r["supports"]))

    def test_invalidation_present_for_bull(self):
        r = build_macro_reasoning(_inputs(regime="bull", usdkrw=1400.0))
        self.assertTrue(any("BASE 강등" in x for x in r["invalidation"]))
        self.assertTrue(any("환율" in x for x in r["invalidation"]))


if __name__ == "__main__":
    unittest.main()
