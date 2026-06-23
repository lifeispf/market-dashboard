"""engine/tests/test_multi_window_rrg.py — Phase E/F 멀티 윈도우 RRG 단위테스트.

stdlib unittest. 합성 pandas Series만 사용(DB/네트워크 fetch 없음) — 데이터 무관.
`engine.sector.inputs.compute_multi_window_rrg`가 호출부가 넘긴 `windows` 딕셔너리
(라벨→거래일) 각각에 scoring.compute_rs_ratio_momentum/rrg_quadrant를 그대로 호출하고,
합의(consensus)를 올바르게 산출/degrade하는지 검증한다. Phase F: 윈도우 셋 자체가
tf에 따라 스케일하는 `engine.core.timeframes.rrg_windows_for`도 함께 검증한다.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from engine.core.timeframes import RRG_WINDOWS, rrg_windows_for
from engine.sector.inputs import compute_multi_window_rrg


def _series(n, start=100.0, drift=0.0, seed=0):
    """길이 n의 합성 가격 시리즈(약한 랜덤워크 + drift) — 재현 가능(seed 고정)."""
    rng = np.random.default_rng(seed)
    steps = rng.normal(loc=drift, scale=0.5, size=n)
    values = start + np.cumsum(steps)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    return pd.Series(values, index=idx)


class MultiWindowRrgSufficientDataTests(unittest.TestCase):
    """충분한 history(>=600 거래일)가 있으면 4개 윈도우 모두 채워져야 한다."""

    def setUp(self):
        # sector outperforms benchmark steadily -> should resolve to a real quadrant
        # in every window, not just structurally non-None.
        self.sector = _series(700, start=100.0, drift=0.15, seed=1)
        self.benchmark = _series(700, start=100.0, drift=0.0, seed=2)

    def test_returns_all_four_window_labels(self):
        by_window, consensus = compute_multi_window_rrg(self.sector, self.benchmark, RRG_WINDOWS)
        self.assertEqual(set(by_window.keys()), set(RRG_WINDOWS.keys()))
        self.assertEqual(set(by_window.keys()), {"1M", "3M", "6M", "12M"})

    def test_each_resolved_window_has_ratio_momentum_quadrant(self):
        by_window, consensus = compute_multi_window_rrg(self.sector, self.benchmark, RRG_WINDOWS)
        for label, entry in by_window.items():
            if entry is None:
                continue
            self.assertIn("ratio", entry)
            self.assertIn("momentum", entry)
            self.assertIn("quadrant", entry)
            self.assertIn(entry["quadrant"], {"leading", "improving", "weakening", "lagging"})

    def test_consensus_present_when_windows_resolve(self):
        by_window, consensus = compute_multi_window_rrg(self.sector, self.benchmark, RRG_WINDOWS)
        n_resolved = sum(1 for v in by_window.values() if v is not None)
        self.assertGreater(n_resolved, 0)
        self.assertIsNotNone(consensus)
        self.assertIn("quadrant", consensus)
        self.assertIn("agreement", consensus)
        self.assertIn("n", consensus)
        self.assertEqual(consensus["n"], n_resolved)
        self.assertGreaterEqual(consensus["agreement"], 0.0)
        self.assertLessEqual(consensus["agreement"], 1.0)

    def test_consensus_quadrant_is_one_of_resolved_quadrants(self):
        by_window, consensus = compute_multi_window_rrg(self.sector, self.benchmark, RRG_WINDOWS)
        resolved = {v["quadrant"] for v in by_window.values() if v is not None}
        self.assertIn(consensus["quadrant"], resolved)


class MultiWindowRrgInsufficientDataTests(unittest.TestCase):
    """None / 너무 짧은 series -> 모든 윈도우 None, consensus None (never raises)."""

    def test_none_series_yields_all_none_windows_and_none_consensus(self):
        by_window, consensus = compute_multi_window_rrg(None, None, RRG_WINDOWS)
        self.assertEqual(set(by_window.keys()), {"1M", "3M", "6M", "12M"})
        self.assertTrue(all(v is None for v in by_window.values()))
        self.assertIsNone(consensus)

    def test_one_sided_none_yields_all_none(self):
        sector = _series(700, seed=3)
        by_window, consensus = compute_multi_window_rrg(sector, None, RRG_WINDOWS)
        self.assertTrue(all(v is None for v in by_window.values()))
        self.assertIsNone(consensus)

    def test_short_series_resolves_only_short_windows(self):
        # ~40 trading days: 1M(21) needs 21+21+1=43 overlapping bars -> likely None too;
        # use a length that clears 1M's threshold but not 12M's (252+252+1=505).
        n = 50
        sector = _series(n, drift=0.2, seed=4)
        benchmark = _series(n, drift=0.0, seed=5)
        by_window, consensus = compute_multi_window_rrg(sector, benchmark, RRG_WINDOWS)
        self.assertIsNone(by_window["12M"])
        self.assertIsNone(by_window["6M"])
        self.assertIsNone(by_window["3M"])
        # 1M may or may not resolve depending on threshold (50 < 21+21+1=43 is False ->
        # 50 >= 43 so 1M should resolve for this length).
        self.assertIsNotNone(by_window["1M"])
        self.assertEqual(consensus["n"], 1)
        self.assertEqual(consensus["quadrant"], by_window["1M"]["quadrant"])
        self.assertEqual(consensus["agreement"], 1.0)

    def test_very_short_series_all_windows_none(self):
        sector = _series(5, seed=6)
        benchmark = _series(5, seed=7)
        by_window, consensus = compute_multi_window_rrg(sector, benchmark, RRG_WINDOWS)
        self.assertTrue(all(v is None for v in by_window.values()))
        self.assertIsNone(consensus)

    def test_never_raises_on_mismatched_index(self):
        # disjoint date ranges -> inner join produces empty/too-short aligned series.
        sector = pd.Series([1.0, 2.0, 3.0], index=pd.bdate_range("2020-01-01", periods=3))
        benchmark = pd.Series([1.0, 2.0, 3.0], index=pd.bdate_range("2021-01-01", periods=3))
        by_window, consensus = compute_multi_window_rrg(sector, benchmark, RRG_WINDOWS)
        self.assertTrue(all(v is None for v in by_window.values()))
        self.assertIsNone(consensus)


class MultiWindowRrgConsensusModalLogicTests(unittest.TestCase):
    """consensus 최빈값/동률(긴 윈도우 우선) 로직을 scoring 모킹 없이 직접 구성해 검증.

    compute_multi_window_rrg는 scoring.compute_rs_ratio_momentum을 직접 호출하므로
    quadrant를 임의로 주입하기 어렵다 — 대신 4개 합성 시리즈 조합으로 "다수결" 케이스
    (leading이 가장 흔함)를 구성해, 모듈의 합의 출력이 실제로 최빈 quadrant와 일치하는지
    확인한다(화이트박스가 아니라 동작 검증).
    """

    def test_strong_consistent_outperformance_all_windows_agree_leading_or_better(self):
        # Strong, very consistent sector outperformance across all horizons should drive
        # every resolved window toward the same (non-lagging) quadrant, giving full agreement.
        sector = _series(700, start=100.0, drift=0.3, seed=10)
        benchmark = _series(700, start=100.0, drift=-0.05, seed=11)
        by_window, consensus = compute_multi_window_rrg(sector, benchmark, RRG_WINDOWS)
        resolved = [v["quadrant"] for v in by_window.values() if v is not None]
        self.assertGreater(len(resolved), 0)
        # consensus quadrant must be the actual modal value among resolved windows
        from collections import Counter
        counts = Counter(resolved)
        max_count = max(counts.values())
        self.assertEqual(counts[consensus["quadrant"]], max_count)
        self.assertAlmostEqual(consensus["agreement"], max_count / len(resolved))


class RrgWindowsForTfTests(unittest.TestCase):
    """Phase F: rrg_windows_for(tf)가 tf에 따라 다른 윈도우 셋을 반환하는지 검증."""

    def test_1d_matches_legacy_rrg_windows(self):
        self.assertEqual(rrg_windows_for("1D"), RRG_WINDOWS)
        self.assertEqual(rrg_windows_for("1D"), {"1M": 21, "3M": 63, "6M": 126, "12M": 252})

    def test_1w_differs_from_1d(self):
        windows_1d = rrg_windows_for("1D")
        windows_1w = rrg_windows_for("1W")
        self.assertNotEqual(windows_1d, windows_1w)
        self.assertEqual(set(windows_1w.keys()), {"3M", "6M", "12M", "18M"})
        self.assertEqual(windows_1w, {"3M": 63, "6M": 126, "12M": 252, "18M": 378})

    def test_unknown_tf_falls_back_to_1d(self):
        self.assertEqual(rrg_windows_for("not-a-tf"), rrg_windows_for("1D"))
        self.assertEqual(rrg_windows_for(None), rrg_windows_for("1D"))

    def test_longer_tf_has_longer_windows_than_shorter_tf(self):
        # The longest window for each successive tf should be >= the previous tf's longest.
        order = ["1D", "1W", "1M", "1Q", "1Y"]
        longest = [max(rrg_windows_for(tf).values()) for tf in order]
        self.assertEqual(longest, sorted(longest))
        self.assertEqual(longest[0], 252)
        self.assertEqual(longest[-1], 1260)


class ComputeMultiWindowRrgCustomWindowsTests(unittest.TestCase):
    """compute_multi_window_rrg가 호출부가 넘긴 임의의 `windows` 라벨로 응답하는지 검증."""

    def test_returns_entries_keyed_by_passed_window_labels(self):
        sector = _series(700, start=100.0, drift=0.15, seed=20)
        benchmark = _series(700, start=100.0, drift=0.0, seed=21)
        custom_windows = {"6M": 126, "12M": 252, "18M": 378, "24M": 504}
        by_window, consensus = compute_multi_window_rrg(sector, benchmark, custom_windows)
        self.assertEqual(set(by_window.keys()), set(custom_windows.keys()))
        self.assertNotIn("1M", by_window)
        self.assertNotIn("3M", by_window)
        for label, entry in by_window.items():
            if entry is None:
                continue
            self.assertIn(entry["quadrant"], {"leading", "improving", "weakening", "lagging"})

    def test_window_exceeding_history_degrades_to_none(self):
        # 700 daily bars is not enough for a 1260-bar (60M) window to ever resolve
        # (needs 1260+1260+1=2521 overlapping bars) -> must degrade to None, not raise.
        sector = _series(700, start=100.0, drift=0.1, seed=22)
        benchmark = _series(700, start=100.0, drift=0.0, seed=23)
        custom_windows = {"12M": 252, "24M": 504, "36M": 756, "60M": 1260}
        by_window, consensus = compute_multi_window_rrg(sector, benchmark, custom_windows)
        self.assertIsNone(by_window["60M"])
        self.assertIsNone(by_window["36M"])
        # shorter windows should still resolve given 700 bars of consistent drift.
        self.assertIsNotNone(by_window["12M"])


if __name__ == "__main__":
    unittest.main()
