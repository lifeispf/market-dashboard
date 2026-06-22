"""engine/tests/test_sector_engine.py — Stage 4 Sector Engine 검증.

stdlib unittest. 두 갈래를 검증한다:
1. 단위(데이터 무관): 더미 SectorRow를 §21 모듈+SectorRulebook에 흘려
   quadrant -> State/Transition/Verdict 매핑이 의도대로인지, degrade(None)가
   안전한지.
2. 통합(라이브, 환경 의존): run_sectors가 두 market에서 EngineOutput 리스트를
   내고 JSON 직렬화되는지. 데이터가 없어도(키 없음) 크래시하지 않고 degrade.
"""
from __future__ import annotations

import json
import unittest

from engine.core.context import Context
from engine.core.contracts import EngineOutput, Verdict
from engine.sector.classification import classify
from engine.sector.engine import build_sector_engine, run_sectors
from engine.sector.inputs import SectorRow, sector_rows_to_payload


class SectorRelativeStrengthMappingTests(unittest.TestCase):
    """§21 quadrant -> State/Transition/Verdict 매핑(데이터 무관)."""

    def _run_one(self, quadrant, rs_ratio=105.0, rs_momentum=102.0) -> EngineOutput:
        engine = build_sector_engine()
        row = SectorRow(
            code="semi", name="반도체", market_cap=1e12,
            ytd=12.3, rs_ratio=rs_ratio, rs_momentum=rs_momentum, quadrant=quadrant,
        )
        return engine.run(row.code, Context.root("KOSPI"), data=row)

    def test_leading_is_strong_up_strong_leader(self):
        out = self._run_one("leading")
        self.assertEqual(out.tier, "sector")
        self.assertEqual(out.entity_id, "semi")
        self.assertEqual(out.verdict.direction, "strong_up")
        self.assertEqual(out.verdict.strength, 4)
        self.assertEqual(out.verdict.lead_pattern, "Strong Leader")
        self.assertEqual(out.modules[0].state, "Leader")

    def test_improving_is_up_early_rotation(self):
        out = self._run_one("improving")
        self.assertEqual(out.verdict.direction, "up")
        self.assertEqual(out.verdict.lead_pattern, "Early Rotation")
        self.assertEqual(out.modules[0].state, "Emerging")

    def test_weakening_is_late_leader_neutral(self):
        out = self._run_one("weakening")
        self.assertEqual(out.verdict.direction, "neutral")
        self.assertEqual(out.verdict.lead_pattern, "Late Leader")
        # State stays Leader (still high RS) but transition flags the late phase.
        self.assertEqual(out.modules[0].state, "Leader")
        self.assertEqual(out.modules[0].transition, "Weakening")

    def test_lagging_is_down_breakdown(self):
        out = self._run_one("lagging")
        self.assertEqual(out.verdict.direction, "down")
        self.assertEqual(out.verdict.lead_pattern, "Breakdown")
        self.assertEqual(out.modules[0].state, "Lagging")

    def test_leading_has_offensive_risk_profile(self):
        out = self._run_one("leading")
        self.assertEqual(out.verdict.extra["risk_profile"], "offensive")

    def test_none_quadrant_degrades_safely(self):
        out = self._run_one(None, rs_ratio=None, rs_momentum=None)
        self.assertEqual(out.verdict.direction, "neutral")
        self.assertEqual(out.verdict.strength, 0)
        self.assertIsNone(out.modules[0].state)
        # mode must be "degraded" when the module observed nothing.
        self.assertEqual(out.mode, "degraded")
        # risk_profile is static classification metadata — must survive degrade.
        self.assertEqual(out.verdict.extra["risk_profile"], "offensive")

    def test_macro_upstream_noted_in_narrative(self):
        engine = build_sector_engine()
        row = SectorRow("semi", "반도체", 1e12, 12.3, 105.0, 102.0, "leading")
        macro_verdict = Verdict(
            direction="up", strength=3, conviction=None, lead_pattern="bull",
            narrative="macro", horizon="T1",
        )
        ctx = Context(market="KOSPI", upstream={"macro": macro_verdict})
        out = engine.run("semi", ctx, data=row)
        self.assertIn("macro regime", out.verdict.narrative)


class SectorRiskProfileClassificationTests(unittest.TestCase):
    """engine.sector.classification — 정적 위험선호 분류(데이터 무관)."""

    def test_classify_known_defensive_code(self):
        self.assertEqual(classify("Util"), "defensive")

    def test_classify_unknown_code_defaults_neutral(self):
        self.assertEqual(classify("unknown_code"), "neutral")


class SectorPayloadMappingTests(unittest.TestCase):
    def test_sector_rows_to_payload_shape(self):
        rows = [SectorRow("semi", "반도체", 1e12, 12.3, 105.0, 102.0, "leading")]
        out = sector_rows_to_payload(rows)
        self.assertEqual(
            out[0],
            {"code": "semi", "name": "반도체", "marketCap": 1e12, "ytd": 12.3,
             "rsRatio": 105.0, "rsMomentum": 102.0, "quadrant": "leading"},
        )


class SectorEngineLiveSmokeTests(unittest.TestCase):
    """라이브 통합 — 환경 데이터에 의존(키 없으면 degrade). 크래시만 안 나면 OK."""

    def test_run_sectors_kospi_serializable(self):
        outputs = run_sectors("KOSPI")
        self.assertIsInstance(outputs, list)
        self.assertGreater(len(outputs), 0)
        for eo in outputs:
            self.assertEqual(eo.tier, "sector")
            json.dumps(eo.to_dict())  # 직렬화 가능해야 한다

    def test_run_sectors_nasdaq_serializable(self):
        outputs = run_sectors("NASDAQ")
        self.assertIsInstance(outputs, list)
        self.assertGreater(len(outputs), 0)
        for eo in outputs:
            json.dumps(eo.to_dict())


if __name__ == "__main__":
    unittest.main()
