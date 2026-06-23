"""engine/tests/test_concentration.py — Phase D-⑤ 집중도/리더십 협소도 단위테스트.

stdlib unittest. 데이터 무관(합성 SectorRow/dict 입력) — DB/네트워크 fetch 없음.
"""
from __future__ import annotations

import unittest

from engine.sector.concentration import compute_concentration
from engine.sector.inputs import SectorRow


def _row(code, name, cap, ytd):
    return SectorRow(
        code=code, name=name, market_cap=cap, ytd=ytd,
        rs_ratio=None, rs_momentum=None, quadrant=None,
    )


class ConcentrationEmptyDegradeTests(unittest.TestCase):
    def test_empty_rows_all_none(self):
        out = compute_concentration([])
        self.assertIsNone(out["hhi"])
        self.assertIsNone(out["effective_n"])
        self.assertIsNone(out["top1_cap_pct"])
        self.assertIsNone(out["top3_cap_pct"])
        self.assertIsNone(out["top1_ytd_contribution_pct"])
        self.assertIsNone(out["top3_ytd_contribution_pct"])
        self.assertEqual(out["leaders"], [])

    def test_all_caps_none_degrades(self):
        rows = [_row("a", "A", None, 5.0), _row("b", "B", None, -3.0)]
        out = compute_concentration(rows)
        self.assertIsNone(out["hhi"])
        self.assertIsNone(out["effective_n"])
        self.assertEqual(out["leaders"], [])

    def test_never_raises_on_bad_types(self):
        # non-numeric cap/ytd must degrade gracefully, never raise.
        rows = [
            {"name": "Weird", "market_cap": "not-a-number", "ytd": "nope"},
            _row("ok", "OK", 100.0, 10.0),
        ]
        out = compute_concentration(rows)  # should not raise
        self.assertIsNotNone(out["hhi"])


class ConcentrationKnownValuesTests(unittest.TestCase):
    def test_equal_caps_four_sectors_hhi_quarter(self):
        rows = [_row(c, c, 100.0, 0.0) for c in ["a", "b", "c", "d"]]
        out = compute_concentration(rows)
        self.assertAlmostEqual(out["hhi"], 0.25)
        self.assertAlmostEqual(out["effective_n"], 4.0)
        self.assertAlmostEqual(out["top1_cap_pct"], 25.0)
        self.assertAlmostEqual(out["top3_cap_pct"], 75.0)

    def test_single_sector_dominates_hhi_one(self):
        rows = [_row("semi", "반도체", 900.0, 50.0), _row("etc", "Etc", 100.0, 1.0)]
        out = compute_concentration(rows)
        self.assertAlmostEqual(out["hhi"], 0.81 + 0.01)  # (0.9^2 + 0.1^2)
        self.assertAlmostEqual(out["effective_n"], 1.0 / (0.81 + 0.01))
        self.assertAlmostEqual(out["top1_cap_pct"], 90.0)
        self.assertEqual(out["leaders"][0], "반도체")

    def test_top3_cap_pct_caps_at_total_when_fewer_than_three_rows(self):
        rows = [_row("a", "A", 60.0, 1.0), _row("b", "B", 40.0, 1.0)]
        out = compute_concentration(rows)
        self.assertAlmostEqual(out["top3_cap_pct"], 100.0)

    def test_leaders_limited_to_three_sorted_by_cap_desc(self):
        rows = [
            _row("a", "A", 10.0, 1.0), _row("b", "B", 50.0, 1.0),
            _row("c", "C", 30.0, 1.0), _row("d", "D", 5.0, 1.0),
        ]
        out = compute_concentration(rows)
        self.assertEqual(out["leaders"], ["B", "C", "A"])

    def test_negative_or_zero_cap_excluded(self):
        rows = [_row("a", "A", 0.0, 1.0), _row("b", "B", -5.0, 1.0), _row("c", "C", 100.0, 1.0)]
        out = compute_concentration(rows)
        self.assertAlmostEqual(out["hhi"], 1.0)
        self.assertEqual(out["leaders"], ["C"])


class ConcentrationYtdContributionTests(unittest.TestCase):
    def test_single_dominant_leader_contribution_near_100(self):
        # semi: 50% cap weight, +158% YTD -> dominates positive contribution sum.
        rows = [
            _row("semi", "반도체", 500.0, 158.0),
            _row("fin", "금융", 500.0, 2.0),
        ]
        out = compute_concentration(rows)
        # contributions: semi = 0.5*158=79.0, fin = 0.5*2=1.0; sum=80.0
        self.assertAlmostEqual(out["top1_ytd_contribution_pct"], 79.0 / 80.0 * 100.0)
        self.assertAlmostEqual(out["top3_ytd_contribution_pct"], 100.0)
        self.assertEqual(out["leaders"][0], "반도체")  # by cap, tied here but stable order

    def test_negative_contributions_excluded_from_denominator(self):
        rows = [
            _row("a", "A", 100.0, 50.0),   # contribution = 0.5*50=25 (cap 100/200=0.5)
            _row("b", "B", 100.0, -50.0),  # contribution negative -> excluded from positive sum
        ]
        out = compute_concentration(rows)
        # only positive contribution: A=25 -> top1 share of positive sum = 100%
        self.assertAlmostEqual(out["top1_ytd_contribution_pct"], 100.0)

    def test_rows_missing_ytd_skipped_in_contribution(self):
        rows = [
            _row("a", "A", 100.0, None),
            _row("b", "B", 100.0, 10.0),
        ]
        out = compute_concentration(rows)
        # only B contributes -> top1 = 100% of positive sum
        self.assertAlmostEqual(out["top1_ytd_contribution_pct"], 100.0)

    def test_all_ytd_missing_or_nonpositive_yields_none_contribution(self):
        rows = [_row("a", "A", 100.0, None), _row("b", "B", 100.0, -5.0)]
        out = compute_concentration(rows)
        self.assertIsNone(out["top1_ytd_contribution_pct"])
        self.assertIsNone(out["top3_ytd_contribution_pct"])

    def test_dict_input_camel_case_supported(self):
        rows = [
            {"name": "반도체", "marketCap": 500.0, "ytd": 158.0},
            {"name": "금융", "marketCap": 500.0, "ytd": 2.0},
        ]
        out = compute_concentration(rows)
        self.assertIsNotNone(out["hhi"])
        self.assertAlmostEqual(out["top1_cap_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
