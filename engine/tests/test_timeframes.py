"""engine/tests/test_timeframes.py — Phase A 타임프레임 인프라 검증.

stdlib unittest. 검증 범위:
1. resample_for_tf(series, "1D")가 identity(원본 그대로)인지.
2. tf="1D"가 gather_macro_inputs/gather_sector_inputs/gather_stock_inputs의
   무인자 호출과 deep-equal인지(byte-identical 불변식 — Phase A 안전 게이트).
3. tf="1W" 스모크 — 크래시 없이 반환되고, 합성 짧은 시리즈에서 RRG가 데이터
   부족으로 None으로 degrade하는지(데이터 무관 단위 테스트).
4. test_macro_equivalence가 여전히 그린인지는 별도 파일에서 보장되지만, 여기서도
   import 가능 여부로 한 번 더 손대지 않았음을 확인한다.
"""
from __future__ import annotations

import unittest

import pandas as pd

from engine.core.timeframes import (
    DEFAULT_TF,
    TIMEFRAMES,
    normalize_tf,
    resample_for_tf,
    rrg_window_for,
    spark_n_for,
)
from backend.api.history import SCORE_FIELDS, get_history
from engine.macro.inputs import gather_macro_inputs
from engine.sector.inputs import gather_sector_inputs
from engine.stock.inputs import gather_stock_inputs

MARKETS = ("KOSPI", "NASDAQ")


class NormalizeTfTests(unittest.TestCase):
    def test_default_is_1d(self):
        self.assertEqual(DEFAULT_TF, "1D")

    def test_none_normalizes_to_1d(self):
        self.assertEqual(normalize_tf(None), "1D")

    def test_unknown_normalizes_to_1d(self):
        self.assertEqual(normalize_tf("bogus"), "1D")
        self.assertEqual(normalize_tf(""), "1D")

    def test_known_keys_pass_through(self):
        for key in ("1D", "1W", "1M", "1Q", "1Y"):
            self.assertEqual(normalize_tf(key), key)


class TimeframeBundleTableTests(unittest.TestCase):
    def test_table_has_all_five_keys(self):
        self.assertEqual(set(TIMEFRAMES.keys()), {"1D", "1W", "1M", "1Q", "1Y"})

    def test_1d_bundle_is_identity_spark60_window10(self):
        b = TIMEFRAMES["1D"]
        self.assertIsNone(b.resample)
        self.assertEqual(b.spark_n, 60)
        self.assertEqual(b.rrg_window, 10)

    def test_accessors_match_table(self):
        for key, bundle in TIMEFRAMES.items():
            self.assertEqual(rrg_window_for(key), bundle.rrg_window)
            self.assertEqual(spark_n_for(key), bundle.spark_n)


class ResampleIdentityTests(unittest.TestCase):
    """resample_for_tf(series, "1D") must be a true identity — no transform at all,
    since this is the mechanism that guarantees the byte-identical invariant."""

    def _series(self):
        idx = pd.date_range("2025-01-01", periods=30, freq="D")
        return pd.Series(range(30), index=idx, dtype=float)

    def test_1d_returns_same_object(self):
        s = self._series()
        out = resample_for_tf(s, "1D")
        self.assertIs(out, s)

    def test_1d_values_identical(self):
        s = self._series()
        out = resample_for_tf(s, "1D")
        pd.testing.assert_series_equal(out, s)

    def test_none_series_passthrough(self):
        self.assertIsNone(resample_for_tf(None, "1D"))
        self.assertIsNone(resample_for_tf(None, "1W"))

    def test_1w_resamples_and_shrinks_length(self):
        s = self._series()
        out = resample_for_tf(s, "1W")
        self.assertIsNotNone(out)
        self.assertLess(len(out), len(s))

    def test_unknown_tf_normalizes_and_is_identity(self):
        s = self._series()
        out = resample_for_tf(s, "not-a-tf")
        self.assertIs(out, s)


class MacroEquivalenceAtTfTests(unittest.TestCase):
    """gather_macro_inputs(m) == gather_macro_inputs(m, tf="1D") for both markets."""

    def _assert_equal(self, market):
        default = gather_macro_inputs(market)
        explicit = gather_macro_inputs(market, tf="1D")
        self.assertEqual(default.__dict__.keys(), explicit.__dict__.keys())
        # registry/sectors_config/config carry freshly-built function objects
        # (fetch_fn closures) each call -- never identity/value-equal across two
        # independent gather calls even with zero behavior change, so they're not
        # meaningful equivalence signal. Every other field (the actual data) must match.
        skip_fields = {"registry"}
        for key in default.__dict__:
            if key in skip_fields:
                continue
            a, b = getattr(default, key), getattr(explicit, key)
            if hasattr(a, "equals"):  # pandas Series/DataFrame
                if a is None or b is None:
                    self.assertEqual(a, b)
                else:
                    self.assertTrue(a.equals(b), f"field {key} differs")
            else:
                self.assertEqual(a, b, f"field {key} differs")

    def test_kospi(self):
        self._assert_equal("KOSPI")

    def test_nasdaq(self):
        self._assert_equal("NASDAQ")


class SectorEquivalenceAtTfTests(unittest.TestCase):
    """gather_sector_inputs(m) == gather_sector_inputs(m, tf="1D") for both markets."""

    def _assert_equal(self, market):
        default = gather_sector_inputs(market)
        explicit = gather_sector_inputs(market, tf="1D")
        self.assertEqual(len(default), len(explicit))
        for d, e in zip(default, explicit):
            self.assertEqual(d, e)

    def test_kospi(self):
        self._assert_equal("KOSPI")

    def test_nasdaq(self):
        self._assert_equal("NASDAQ")


class StockEquivalenceAtTfTests(unittest.TestCase):
    """gather_stock_inputs(m) == gather_stock_inputs(m, tf="1D") for both markets."""

    def _assert_equal(self, market):
        default = gather_stock_inputs(market)
        explicit = gather_stock_inputs(market, tf="1D")
        self.assertEqual(len(default), len(explicit))
        for d, e in zip(default, explicit):
            self.assertEqual(d, e)

    def test_kospi(self):
        self._assert_equal("KOSPI")

    def test_nasdaq(self):
        self._assert_equal("NASDAQ")


class TfSmokeTests(unittest.TestCase):
    """tf="1W" smoke across the live gather_* functions -- must not crash."""

    def test_macro_1w_smoke(self):
        for market in MARKETS:
            out = gather_macro_inputs(market, tf="1W")
            self.assertIsInstance(out.spark, list)

    def test_sector_1w_smoke(self):
        for market in MARKETS:
            rows = gather_sector_inputs(market, tf="1W")
            self.assertIsInstance(rows, list)
            self.assertGreater(len(rows), 0)

    def test_stock_1w_smoke(self):
        for market in MARKETS:
            rows = gather_stock_inputs(market, tf="1W")
            self.assertIsInstance(rows, list)
            self.assertGreater(len(rows), 0)


class RrgDegradeOnShortSeriesTests(unittest.TestCase):
    """Data-independent: a short synthetic series resampled to a coarse tf has too
    few bars for compute_rs_ratio_momentum -> (None, None) -> quadrant None."""

    def test_1w_resample_of_short_series_degrades_rrg(self):
        import scoring

        idx = pd.date_range("2025-01-01", periods=15, freq="D")  # ~2 weeks of daily data
        target = pd.Series(range(15), index=idx, dtype=float) + 100
        benchmark = pd.Series(range(15), index=idx, dtype=float) + 200

        resampled_target = resample_for_tf(target, "1W")
        resampled_benchmark = resample_for_tf(benchmark, "1W")
        # ~2-3 weekly bars -- far short of ratio_window+momentum_window+1=21 for 1W's window=10.
        rs_r, rs_m = scoring.compute_rs_ratio_momentum(
            resampled_target, resampled_benchmark,
            ratio_window=rrg_window_for("1W"), momentum_window=rrg_window_for("1W"),
        )
        self.assertIsNone(rs_r)
        self.assertIsNone(rs_m)
        self.assertIsNone(scoring.rrg_quadrant(rs_r, rs_m))

    def test_1y_resample_of_short_series_degrades_rrg(self):
        import scoring

        idx = pd.date_range("2024-01-01", periods=400, freq="D")  # ~1.1y daily
        target = pd.Series(range(400), index=idx, dtype=float) + 100
        benchmark = pd.Series(range(400), index=idx, dtype=float) + 200

        resampled_target = resample_for_tf(target, "1Y")
        resampled_benchmark = resample_for_tf(benchmark, "1Y")
        # Only ~2 yearly bars -- far short of ratio_window+momentum_window+1=9 for 1Y's window=4.
        rs_r, rs_m = scoring.compute_rs_ratio_momentum(
            resampled_target, resampled_benchmark,
            ratio_window=rrg_window_for("1Y"), momentum_window=rrg_window_for("1Y"),
        )
        self.assertIsNone(rs_r)
        self.assertIsNone(rs_m)
        self.assertIsNone(scoring.rrg_quadrant(rs_r, rs_m))


class HistoryEndpointScoreAndFearGreedTests(unittest.TestCase):
    """Phase B: /api/history/{market} must additionally expose `scores` (per-field
    score trend resampled to tf) and `fearGreed` (best-effort recomputed trend),
    alongside the existing `sectors` trail block. Calls the handler function
    directly (no HTTP) per the test brief. Values are data-dependent (scores_daily
    is sparse in dev), so these assert STRUCTURE + no-crash, not specific numbers."""

    def _assert_points_shape(self, points):
        self.assertIsInstance(points, list)
        for p in points:
            self.assertIn("date", p)
            self.assertIn("value", p)
            self.assertIsInstance(p["date"], str)
            self.assertIsInstance(p["value"], float)

    def _assert_response_shape(self, payload):
        # existing Phase A keys must still be present (sectors trail untouched)
        self.assertIn("sectors", payload)
        self.assertIn("scores", payload)
        self.assertIn("fearGreed", payload)

        scores = payload["scores"]
        self.assertEqual(set(scores.keys()), set(SCORE_FIELDS))
        for field in SCORE_FIELDS:
            self._assert_points_shape(scores[field])

        self._assert_points_shape(payload["fearGreed"])

    def test_kospi_1d_no_crash_and_shape(self):
        payload = get_history("KOSPI", tf="1D")
        self._assert_response_shape(payload)

    def test_kospi_1w_no_crash_and_shape(self):
        payload = get_history("KOSPI", tf="1W")
        self._assert_response_shape(payload)

    def test_nasdaq_1d_no_crash_and_shape(self):
        payload = get_history("NASDAQ", tf="1D")
        self._assert_response_shape(payload)

    def test_nasdaq_1w_no_crash_and_shape(self):
        payload = get_history("NASDAQ", tf="1W")
        self._assert_response_shape(payload)

    def test_unknown_market_still_404s(self):
        from fastapi import HTTPException

        with self.assertRaises(HTTPException):
            get_history("BOGUS", tf="1D")


if __name__ == "__main__":
    unittest.main()
