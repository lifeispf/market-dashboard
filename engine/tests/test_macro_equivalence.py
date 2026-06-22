"""engine/tests/test_macro_equivalence.py — Stage 2 byte-identical regression gate.

stdlib unittest (venv에 pytest 미설치). 작업 지시(00_architecture.md §11)의
유일한 성공 기준: GET /api/market/{market}가 반환하는 dict이 리트로핏 전후로
완전히 동일해야 한다. 이 테스트는 KOSPI와 NASDAQ 각각에 대해 새 엔진 경로
(backend/api/market.py:_assemble_live, 이제 engine/macro/를 경유)와 영원히
동결된 오라클(backend/api/_reference_assembly.py:assemble_live_reference)의
전체 payload dict를 deep-equal로 비교한다.
"""

from __future__ import annotations

import unittest

from backend.api._reference_assembly import assemble_live_reference
from backend.api.market import _assemble_live


class MacroEquivalenceTests(unittest.TestCase):
    """새 engine-routed _assemble_live가 동결 오라클과 byte-identical인지 검증."""

    def test_kospi_byte_identical(self):
        new_payload = _assemble_live("KOSPI")
        ref_payload = assemble_live_reference("KOSPI")
        self.assertEqual(new_payload, ref_payload)

    def test_nasdaq_byte_identical(self):
        new_payload = _assemble_live("NASDAQ")
        ref_payload = assemble_live_reference("NASDAQ")
        self.assertEqual(new_payload, ref_payload)


if __name__ == "__main__":
    unittest.main()
