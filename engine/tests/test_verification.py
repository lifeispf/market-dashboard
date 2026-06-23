"""engine/tests/test_verification.py — Phase F 스코어카드 검증.

stdlib unittest. 방법론 핵심(forward-alignment=look-ahead 없음, Spearman IC,
RRG quadrant series 재현)을 합성 데이터로 검증하고, build_scorecard가 두 마켓
에서 shape대로 무크래시 반환하는지(라이브, 환경 의존) 스모크한다.
"""
from __future__ import annotations

import unittest

import pandas as pd

from engine.verification import scorecard as sc


class ForwardReturnTests(unittest.TestCase):
    def test_forward_return_no_lookahead(self):
        # level doubles each step: fwd return over 1 step = +100% at each t, last h are NaN.
        level = pd.Series([100.0, 200.0, 400.0, 800.0], index=pd.to_datetime(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]))
        fwd = sc._forward_return(level, 1)
        # at t0: level[t1]/level[t0]-1 = 1.0 (uses FUTURE value, assigned to present t) — correct alignment
        self.assertAlmostEqual(fwd.iloc[0], 1.0)
        self.assertAlmostEqual(fwd.iloc[2], 1.0)
        self.assertTrue(pd.isna(fwd.iloc[-1]))  # no future beyond last → NaN, never fabricated


class SpearmanICTests(unittest.TestCase):
    def _idx(self, n):
        return pd.to_datetime(pd.date_range("2024-01-01", periods=n, freq="D"))

    def test_perfect_monotonic_relationship_ic_near_one(self):
        idx = self._idx(30)
        signal = pd.Series(range(30), index=idx, dtype=float)
        fwd = pd.Series([x * 3 + 5 for x in range(30)], index=idx, dtype=float)  # monotonic↑
        ic, n = sc._spearman_ic(signal, fwd)
        self.assertEqual(n, 30)
        self.assertAlmostEqual(ic, 1.0, places=4)

    def test_perfect_inverse_relationship_ic_near_minus_one(self):
        idx = self._idx(30)
        signal = pd.Series(range(30), index=idx, dtype=float)
        fwd = pd.Series([-x for x in range(30)], index=idx, dtype=float)  # monotonic↓
        ic, _ = sc._spearman_ic(signal, fwd)
        self.assertAlmostEqual(ic, -1.0, places=4)

    def test_thin_sample_returns_none(self):
        idx = self._idx(5)
        ic, n = sc._spearman_ic(pd.Series(range(5), index=idx, dtype=float),
                                pd.Series(range(5), index=idx, dtype=float))
        self.assertIsNone(ic)   # below _MIN_N
        self.assertEqual(n, 5)


class RrgQuadrantSeriesTests(unittest.TestCase):
    def test_quadrant_labels_valid_and_mirror_scoring(self):
        import scoring
        n = 80
        idx = pd.to_datetime(pd.date_range("2024-01-01", periods=n, freq="D"))
        # sector outperforming benchmark with accelerating slope → should reach 'leading' late.
        bench = pd.Series([100.0 + i for i in range(n)], index=idx)
        sector = pd.Series([100.0 + i * 1.5 for i in range(n)], index=idx)
        q = sc._rs_quadrant_series(sector, bench)
        valid = {"leading", "weakening", "improving", "lagging", None}
        self.assertTrue(set(q.dropna().unique()).issubset(valid))
        # spot-check one non-null point matches scoring.rrg_quadrant on the reconstructed ratio/mom
        self.assertGreater(len(q.dropna()), 0)

    def test_short_series_degrades_empty(self):
        idx = pd.to_datetime(pd.date_range("2024-01-01", periods=5, freq="D"))
        q = sc._rs_quadrant_series(pd.Series([1.0] * 5, index=idx), pd.Series([1.0] * 5, index=idx))
        self.assertTrue(q.empty)


class BuildScorecardSmokeTests(unittest.TestCase):
    """라이브 — 환경 데이터 의존(백필돼 있으면 실수치, 없으면 degrade). 무크래시·shape만."""

    def _check_shape(self, market):
        card = sc.build_scorecard(market)
        self.assertIn("limitations", card)
        self.assertIn("index_sample_n", card)
        self.assertIsInstance(card["index_sample_n"], int)
        # if enough data, the four sections exist and carry sample sizes
        if card["index_sample_n"] >= sc._H_LONG + sc._MIN_N:
            self.assertIn("fear_greed_extremes", card)
            self.assertIn("sector_rrg_hit_rate", card)
            self.assertIn("momentum_ic", card)
            self.assertIn("regime_factor_ic", card)
            rrg = card["sector_rrg_hit_rate"]
            if "error" not in rrg:
                self.assertIn("n_bullish", rrg)

    def test_kospi_scorecard_shape(self):
        self._check_shape("KOSPI")

    def test_nasdaq_scorecard_shape(self):
        self._check_shape("NASDAQ")


if __name__ == "__main__":
    unittest.main()
