from __future__ import annotations

import unittest
from datetime import date

from backend.store import db


TEST_SERIES_ID = "test:ohlc"


def _purge_test_rows():
    db.init_db()
    with db.get_connection() as conn:
        conn.execute("DELETE FROM series_ohlc_daily WHERE series_id = ?", (TEST_SERIES_ID,))


class OhlcStorageTests(unittest.TestCase):
    def setUp(self):
        _purge_test_rows()
        self.addCleanup(_purge_test_rows)

    def test_open_and_close_phase_accumulate_same_market_date(self):
        d = date(2026, 6, 26)

        db.upsert_ohlc_series(
            TEST_SERIES_ID,
            [{"date": d, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 10}],
            source="yfinance",
            fetched_at="2026-06-26T13:45:00",
            phase="open",
        )
        row = db.read_ohlc_series(TEST_SERIES_ID)[0]
        self.assertEqual(row["open"], 100.0)
        self.assertIsNone(row["close"])
        self.assertEqual(row["open_fetched_at"], "2026-06-26T13:45:00")
        self.assertIsNone(row["close_fetched_at"])

        db.upsert_ohlc_series(
            TEST_SERIES_ID,
            [{"date": d, "open": 101.0, "high": 110.0, "low": 95.0, "close": 108.0, "volume": 1000}],
            source="yfinance",
            fetched_at="2026-06-26T22:00:00",
            phase="close",
        )
        row = db.read_ohlc_series(TEST_SERIES_ID)[0]
        self.assertEqual(row["open"], 100.0)
        self.assertEqual(row["high"], 110.0)
        self.assertEqual(row["low"], 95.0)
        self.assertEqual(row["close"], 108.0)
        self.assertEqual(row["volume"], 1000.0)
        self.assertEqual(row["open_fetched_at"], "2026-06-26T13:45:00")
        self.assertEqual(row["close_fetched_at"], "2026-06-26T22:00:00")


if __name__ == "__main__":
    unittest.main()
