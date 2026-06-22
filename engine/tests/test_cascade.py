"""engine/tests/test_cascade.py — Stage(캐스케이드) 검증.

stdlib unittest. run_cascade가 Macro→Sector→Stock을 context 전파로 연결하는지
검증한다. 핵심: 하위 tier의 EngineOutput.context.upstream에 상위 tier verdict가
체인으로 보존되는지(stock에 macro+sector 둘 다). 라이브 데이터 의존이지만 키 없이도
degrade로 통과해야 한다.
"""
from __future__ import annotations

import json
import unittest

from engine.cascade import run_cascade


class CascadeTests(unittest.TestCase):
    def test_kospi_cascade_chain_and_serializable(self):
        c = run_cascade("KOSPI")
        self.assertEqual(c.market, "KOSPI")
        self.assertEqual(c.macro.tier, "macro")
        self.assertTrue(len(c.sectors) > 0)

        # 섹터 context.upstream에 macro가 보존되는지.
        sec0 = c.sectors[0]
        self.assertEqual(sec0.tier, "sector")
        self.assertIn("macro", sec0.context.get("upstream", {}))

        # 종목 context.upstream에 macro+sector 체인이 둘 다 보존되는지(§4.3 핵심).
        if c.stocks:
            stk0 = c.stocks[0]
            self.assertEqual(stk0.tier, "stock")
            upstream = stk0.context.get("upstream", {})
            self.assertIn("macro", upstream)
            self.assertIn("sector", upstream)

        # 전체 직렬화 가능(=/api/briefing 응답 가능).
        json.dumps(c.to_dict())

    def test_nasdaq_cascade_serializable(self):
        c = run_cascade("NASDAQ")
        self.assertEqual(c.market, "NASDAQ")
        self.assertTrue(len(c.sectors) > 0)
        json.dumps(c.to_dict())


if __name__ == "__main__":
    unittest.main()
