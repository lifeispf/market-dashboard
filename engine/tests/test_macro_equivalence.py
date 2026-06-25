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
from unittest.mock import patch

from backend.api._reference_assembly import assemble_live_reference
from backend.api.market import _assemble_live
from backend.store.db import get_connection
from engine.macro import eps_source, kospi_level_source, vkospi_source, inputs as macro_inputs


def _purge_eps_cache():
    """Delete any cached eps:KOSPI / eps:NASDAQ rows.

    engine/macro/inputs.py caches the forward-EPS proxy fetch in series_daily via the
    same read-through helper everything else uses (_cached_series), which short-circuits
    to the already-stored value once fetched_at is today -- regardless of whether the
    fetch_fn is monkeypatched afterwards. In this dev environment a `uvicorn
    backend.main:app` server may be running concurrently and serving real dashboard
    requests, which would otherwise populate a real (non-None) eps:* value for today and
    silently defeat the monkeypatch below via that cache. Purging before AND after each
    test keeps the window in which a concurrent request could repopulate it as small as
    possible (full elimination of the race isn't possible with a shared SQLite file and
    an external writer, but this makes the test self-healing on every run).
    """
    with get_connection() as conn:
        conn.execute("DELETE FROM series_daily WHERE series_id IN ('eps:KOSPI', 'eps:NASDAQ')")
        conn.commit()


class MacroEquivalenceTests(unittest.TestCase):
    """새 engine-routed _assemble_live가 동결 오라클과 byte-identical인지 검증.

    Phase D-②: `engine/macro/inputs.py` now tries a live forward-EPS proxy fetch
    (engine.macro.eps_source.fetch_forward_eps) when no manual override is present.
    That is a DELIBERATE NEW live input -- the frozen oracle (_reference_assembly.py)
    only ever reads EPS via manual.get_override and must never change. So for the
    duration of this byte-identical comparison we monkeypatch the new EPS source to
    return None (its own graceful-degrade value), putting both sides back on equal
    footing: EPS=None on both, which is exactly what this gate was built to validate
    (engine-path/legacy-path logic parity), not the new EPS feature itself.
    """

    def setUp(self):
        _purge_eps_cache()
        patcher = patch.object(eps_source, "fetch_forward_eps", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(_purge_eps_cache)
        # VKOSPI도 EPS와 같은 이유로 중립화 — 동결 오라클은 realized-vol을 쓰므로
        # KRX_API_KEY가 있는 환경에서 VKOSPI가 붙으면 발산한다. None으로 막아
        # 게이트가 검증하려는 로직 패리티(realized-vol 기준)를 유지한다.
        vk_patcher = patch.object(vkospi_source, "fetch_vkospi", return_value=None)
        vk_patcher.start()
        self.addCleanup(vk_patcher.stop)
        # KOSPI 레벨 KRX OpenAPI 보강도 동일 이유로 중립화 — 동결 오라클은 pykrx→Yahoo
        # 시리즈 그대로를 쓰므로, KRX_API_KEY가 있는 환경에서 최신점이 붙으면 asOf/level/
        # 모멘텀이 발산한다. None으로 막아 게이트가 검증하려는 로직 패리티를 유지한다.
        kl_patcher = patch.object(kospi_level_source, "fetch_latest_kospi_level", return_value=None)
        kl_patcher.start()
        self.addCleanup(kl_patcher.stop)

    def test_kospi_byte_identical(self):
        new_payload = _assemble_live("KOSPI")
        ref_payload = assemble_live_reference("KOSPI")
        self.assertEqual(new_payload, ref_payload)

    def test_nasdaq_byte_identical(self):
        new_payload = _assemble_live("NASDAQ")
        ref_payload = assemble_live_reference("NASDAQ")
        self.assertEqual(new_payload, ref_payload)


class ForwardEpsSourceTests(unittest.TestCase):
    """D-② new module: never raises, degrades to None, lights up bands when present."""

    def test_fetch_forward_eps_never_raises_and_returns_none_or_positive_float(self):
        for market in ("NASDAQ", "KOSPI", "UNKNOWN"):
            for level in (None, 0, -5, 100.0, 20000.0):
                try:
                    result = eps_source.fetch_forward_eps(market, level)
                except Exception as e:  # pragma: no cover - the whole point is this never fires
                    self.fail(f"fetch_forward_eps raised {e!r} for market={market} level={level}")
                self.assertTrue(result is None or (isinstance(result, float) and result > 0))

    def test_injected_eps_lights_up_bands_and_position(self):
        # gather_macro_inputs only tries the eps_source fallback when manual.get_override
        # returns None (the real-world default, since config.json has no manual_overrides
        # entry for *_forward_eps in this repo). Inject a fixed positive value and confirm
        # levels/position (-> bands/reconciliation/fwdPER downstream) light up instead of
        # staying null.
        #
        # gather_macro_inputs persists the injected EPS into series_daily (series_id
        # "eps:NASDAQ") via the same-day read-through cache, which would otherwise leak
        # this test's fixed 123.45 into any other test calling gather_macro_inputs("NASDAQ")
        # / _assemble_live("NASDAQ") for the rest of the day (e.g. test_nasdaq_byte_identical
        # above, depending on unittest's run order). Clean the row up afterwards so this
        # test is self-contained.
        self.addCleanup(_purge_eps_cache)

        with patch.object(eps_source, "fetch_forward_eps", return_value=123.45):
            result = macro_inputs.gather_macro_inputs("NASDAQ")
        self.assertIsNotNone(result.forward_eps)
        self.assertIsNotNone(result.levels)
        self.assertIsNotNone(result.position)


if __name__ == "__main__":
    unittest.main()
