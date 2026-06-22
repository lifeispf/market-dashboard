"""engine/tests/test_krx_openapi.py — KRX OpenAPI 파서 단위 테스트(네트워크 무관).

실호출(엔드포인트/필드명)은 이 환경에서 검증 불가하므로, synthetic OutBlock_1
응답으로 **파싱 로직**만 검증한다. 필드명이 실제와 다르면 방어적 _pick이
대체 후보를 시도하고, 그래도 없으면 None → 호출측 폴백. 실엔드포인트 검증은
네트워크 환경에서 krx_openapi.verify_krx_openapi()로 별도 수행.
"""
from __future__ import annotations

import os
import unittest

from data import krx_openapi as ko


class ParserTests(unittest.TestCase):
    def test_index_close_picks_main_kospi_and_parses_commas(self):
        rows = [
            {"IDX_NM": "코스피 200", "CLSPRC_IDX": "420.55"},
            {"IDX_NM": "코스피", "CLSPRC_IDX": "3,150.42"},
        ]
        self.assertAlmostEqual(ko.parse_kospi_index_close(rows), 3150.42)

    def test_index_close_falls_back_to_first_row(self):
        rows = [{"IDX_NM": "코스닥", "CLSPRC_IDX": "1,000.00"}]
        self.assertAlmostEqual(ko.parse_kospi_index_close(rows), 1000.0)

    def test_index_close_empty(self):
        self.assertIsNone(ko.parse_kospi_index_close([]))

    def test_breadth_counts_signs(self):
        rows = [
            {"ISU_ABBRV": "A", "FLUC_RT": "1.2"},
            {"ISU_ABBRV": "B", "FLUC_RT": "-0.5"},
            {"ISU_ABBRV": "C", "FLUC_RT": "0.0"},
            {"ISU_ABBRV": "D", "FLUC_RT": "3.4"},
        ]
        self.assertEqual(ko.breadth_from_stocks(rows), (2, 1))

    def test_breadth_none_when_no_rate_field(self):
        rows = [{"ISU_ABBRV": "A", "SOMETHING": "1"}]
        self.assertIsNone(ko.breadth_from_stocks(rows))

    def test_market_cap_sums_with_commas(self):
        rows = [
            {"ISU_ABBRV": "A", "MKTCAP": "1,000,000"},
            {"ISU_ABBRV": "B", "MKTCAP": "2,500,000"},
        ]
        self.assertAlmostEqual(ko.total_market_cap_from_stocks(rows), 3_500_000.0)

    def test_pick_tries_candidates(self):
        row = {"CMPPREVDD_RT": "2.0"}
        # FLUC_RT 없고 CMPPREVDD_RT 있음 → breadth가 대체 필드로 동작
        self.assertEqual(ko.breadth_from_stocks([row]), (1, 0))

    def test_to_float_handles_pct_and_blank(self):
        self.assertIsNone(ko._to_float(""))
        self.assertIsNone(ko._to_float(None))
        self.assertAlmostEqual(ko._to_float("12.5%"), 12.5)


class NoKeyTests(unittest.TestCase):
    def test_fetchers_return_none_without_key(self):
        saved = os.environ.pop("KRX_API_KEY", None)
        try:
            self.assertFalse(ko.is_enabled())
            self.assertIsNone(ko.fetch_kospi_level())
            self.assertIsNone(ko.fetch_breadth())
            self.assertIsNone(ko.fetch_total_market_cap())
        finally:
            if saved is not None:
                os.environ["KRX_API_KEY"] = saved


if __name__ == "__main__":
    unittest.main()
