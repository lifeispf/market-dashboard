"""engine/tests/test_sector_reasoning.py — 섹터 룰베이스 추론 단위테스트(결정적)."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from engine.sector.reasoning import build_sector_reasoning


def _rs(state="Leader", transition="Stable", narrative="rs", **inputs):
    base = dict(rs_ratio=None, rs_momentum=None, quadrant=None, rrg_consensus=None)
    base.update(inputs)
    return SimpleNamespace(state=state, transition=transition, narrative=narrative, inputs=base)


class SectorReasoningTests(unittest.TestCase):
    def test_none_is_no_data(self):
        r = build_sector_reasoning(None)
        self.assertEqual(r["risks"], ["no_data"])
        self.assertIn("판단 보류", r["narrative"])

    def test_leading_is_support(self):
        r = build_sector_reasoning(_rs(quadrant="leading", rs_ratio=104, rs_momentum=102))
        self.assertTrue(any("주도" in s for s in r["supports"]))
        self.assertTrue(any("상대강도 시장 우위" in s for s in r["supports"]))

    def test_lagging_is_risk(self):
        r = build_sector_reasoning(_rs(state="Lagging", quadrant="lagging", rs_ratio=96))
        self.assertTrue(any("소외" in x for x in r["risks"]))
        self.assertTrue(any("상대강도 시장 열위" in x for x in r["risks"]))

    def test_weak_consensus_is_risk(self):
        r = build_sector_reasoning(_rs(quadrant="leading", rrg_consensus={"quadrant": "leading", "agreement": 0.3}))
        self.assertTrue(any("합의 약함" in x for x in r["risks"]))

    def test_strong_consensus_is_support(self):
        r = build_sector_reasoning(_rs(quadrant="leading", rrg_consensus={"quadrant": "leading", "agreement": 0.9}))
        self.assertTrue(any("일치도 높음" in s for s in r["supports"]))

    def test_invalidation_and_macro_note(self):
        r = build_sector_reasoning(_rs(quadrant="improving"), macro_lead="bull")
        self.assertTrue(any("quadrant 하향" in x for x in r["invalidation"]))
        self.assertIn("macro: bull", r["narrative"])


if __name__ == "__main__":
    unittest.main()
