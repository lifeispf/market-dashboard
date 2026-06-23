"""engine/tests/test_backfill.py — Phase D-⑥ 백필 스크립트 스모크 테스트.

backend/backfill.py는 네트워크 호출(yfinance/FRED/KRX)과 실제 dashboard.db에
기록하는 1회성 스크립트라서, unittest 스위트(매 CI 실행)에서 풀 네트워크 백필을
강제하면 느리고 비결정적이며 실DB를 오염시킨다. 그래서 이 테스트는:
  1) 모듈이 import 가능하고 backfill()의 시그니처가 계약대로인지,
  2) 작은 lookback(5일)으로 실제로 한 번 호출했을 때 네트워크/인증 실패가
     있어도 예외를 던지지 않고 항상 결과 리스트를 돌려주는지
만 검증한다. 행 개수(rows)는 네트워크 의존이라 단언하지 않는다 — 0이어도
(키 없음/네트워크 없음) 정상.
"""
from __future__ import annotations

import inspect
import unittest

from backend import backfill as bf


class BackfillImportTests(unittest.TestCase):
    def test_module_importable_and_function_exists(self):
        self.assertTrue(callable(bf.backfill))
        self.assertTrue(callable(bf.main))

    def test_backfill_signature_has_expected_params(self):
        sig = inspect.signature(bf.backfill)
        params = list(sig.parameters)
        self.assertIn("markets", params)
        self.assertIn("lookback_days", params)
        # defaults documented in the plan: 5yr lookback, both markets
        self.assertEqual(sig.parameters["lookback_days"].default, 1825)
        self.assertEqual(sig.parameters["markets"].default, ("KOSPI", "NASDAQ"))


class BackfillSmokeRunTests(unittest.TestCase):
    def test_small_lookback_run_never_raises_and_returns_results(self):
        """Tiny lookback, real registry, but must not raise even if every fetch fails
        (no network/auth in this environment is an expected, graceful outcome)."""
        try:
            results = bf.backfill(markets=("KOSPI",), lookback_days=5)
        except Exception as exc:  # pragma: no cover - this is exactly what must NOT happen
            self.fail(f"backfill() raised instead of degrading gracefully: {exc}")

        self.assertIsInstance(results, list)
        # Every result must report ok/rows/error regardless of network outcome.
        for r in results:
            self.assertIn("market", r)
            self.assertIn("series_id", r)
            self.assertIn("ok", r)
            self.assertIn("rows", r)
            self.assertIn("error", r)


if __name__ == "__main__":
    unittest.main()
