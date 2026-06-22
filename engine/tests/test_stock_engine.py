"""engine/tests/test_stock_engine.py — Stage 5 Stock Engine 검증.

stdlib unittest. 단위(데이터 무관) + 라이브 스모크(환경 의존). §35 RS × §34 Price
Structure 패턴 매칭, Broken veto, Sector→Stock 캐스케이드 강등, position_size_hint를
검증한다.
"""
from __future__ import annotations

import json
import unittest

from engine.core.context import Context
from engine.core.contracts import EngineOutput, Verdict
from engine.stock.engine import build_stock_engine, run_stocks
from engine.stock.inputs import StockRow


def _row(quadrant=None, trend_dir=None, above_ma200=None, ticker="005930.KS"):
    return StockRow(
        ticker=ticker, name="삼성전자", sector_code="semi", sector_name="반도체",
        price=70000.0, ytd=12.0, rs_ratio=105.0, rs_momentum=102.0,
        quadrant=quadrant, trend_dir=trend_dir, vol=0.2, above_ma200=above_ma200,
    )


class StockPatternTests(unittest.TestCase):
    def _run(self, ctx=None, **kw) -> EngineOutput:
        engine = build_stock_engine()
        row = _row(**kw)
        return engine.run(row.ticker, ctx or Context.root("KOSPI"), data=row)

    def test_leader_constructive_is_trend_leader_full(self):
        out = self._run(quadrant="leading", trend_dir="up", above_ma200=True)
        self.assertEqual(out.tier, "stock")
        self.assertEqual(out.verdict.direction, "strong_up")
        self.assertEqual(out.verdict.lead_pattern, "Trend Leader")
        self.assertEqual(out.verdict.extra["position_size_hint"], "full")

    def test_emerging_constructive_is_early_breakout_half(self):
        out = self._run(quadrant="improving", trend_dir="up", above_ma200=True)
        self.assertEqual(out.verdict.direction, "up")
        self.assertEqual(out.verdict.lead_pattern, "Early Stage Breakout")
        self.assertEqual(out.verdict.extra["position_size_hint"], "half")

    def test_broken_structure_vetoes_long_regardless_of_rs(self):
        # RS leading(강세)이어도 구조 Broken이면 Long 금지(direction down, size avoid).
        out = self._run(quadrant="leading", trend_dir="down", above_ma200=False)
        self.assertEqual(out.verdict.direction, "down")
        self.assertEqual(out.verdict.lead_pattern, "Stage 4 Decline")
        self.assertEqual(out.verdict.extra["position_size_hint"], "avoid")
        self.assertTrue(any("구조 붕괴" in r for r in out.verdict.risks))

    def test_extended_winner_neutral_quarter(self):
        out = self._run(quadrant="leading", trend_dir="down", above_ma200=True)
        self.assertEqual(out.verdict.lead_pattern, "Extended Winner")
        self.assertEqual(out.verdict.direction, "neutral")
        self.assertEqual(out.verdict.extra["position_size_hint"], "quarter")

    def test_no_data_degrades_safely(self):
        out = self._run(quadrant=None, trend_dir=None, above_ma200=None)
        self.assertEqual(out.verdict.direction, "neutral")
        self.assertEqual(out.mode, "degraded")
        self.assertEqual(out.verdict.extra["position_size_hint"], "avoid")

    def test_sector_breakdown_cascade_downgrades(self):
        # 상위 섹터가 Breakdown이면 Trend Leader(strong_up)가 한 단계 강등(up).
        sector_v = Verdict(
            direction="strong_down", strength=1, conviction=None,
            lead_pattern="Breakdown", narrative="sector breakdown", horizon="T1",
        )
        ctx = Context(market="KOSPI", upstream={"sector": sector_v})
        out = self._run(ctx=ctx, quadrant="leading", trend_dir="up", above_ma200=True)
        self.assertEqual(out.verdict.direction, "up")  # strong_up -> up
        self.assertTrue(any("섹터 약세" in r for r in out.verdict.risks))


class StockEngineLiveSmokeTests(unittest.TestCase):
    """라이브 통합 — 환경 데이터 의존(키 없으면 degrade). 크래시만 안 나면 OK."""

    def test_run_stocks_kospi_serializable(self):
        outputs = run_stocks("KOSPI")
        self.assertIsInstance(outputs, list)
        for eo in outputs:
            self.assertEqual(eo.tier, "stock")
            self.assertIn("position_size_hint", eo.verdict.extra)
            json.dumps(eo.to_dict())

    def test_run_stocks_nasdaq_serializable(self):
        outputs = run_stocks("NASDAQ")
        self.assertIsInstance(outputs, list)
        for eo in outputs:
            json.dumps(eo.to_dict())


if __name__ == "__main__":
    unittest.main()
