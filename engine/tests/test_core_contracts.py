"""engine/tests/test_core_contracts.py — Engine Core 통일 계약 단위 테스트.

stdlib unittest로 작성(venv에 pytest 미설치). 더미 Module/Rulebook 구현을
통해 Engine.run()의 절차, available_for 필터링, degraded mode 판정,
Context 캐스케이드 체인 보존, EngineOutput의 재귀 직렬화를 검증한다.
"""

from __future__ import annotations

import json
import unittest

from engine.core.context import Context
from engine.core.contracts import EngineOutput, ModuleOutput, Verdict
from engine.core.engine import Engine


class HealthyModule:
    """정상적으로 state/strength를 산출하는 더미 Module."""

    id = "dummy.healthy"
    tier = "dummy"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id, ctx):
        return []

    def compute(self, entity_id, ctx, data) -> ModuleOutput:
        return ModuleOutput(
            module_id=self.id,
            state="bull",
            transition="improving",
            strength=0.8,
            confidence=0.6,
            narrative="healthy module observes bull state",
            inputs={"raw_score": 80},
        )


class StateOnlyNoConfidenceModule:
    """state는 유효하지만 confidence는 항상 None인 더미 Module.

    macro 모듈(축별 confidence 개념이 없는 §9.1 비검증 휴리스틱 영역)을
    모의한다 — confidence=None이 degraded 오판으로 이어지지 않아야 함을
    검증하기 위한 픽스처."""

    id = "dummy.state_only_no_confidence"
    tier = "dummy"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id, ctx):
        return []

    def compute(self, entity_id, ctx, data) -> ModuleOutput:
        return ModuleOutput(
            module_id=self.id,
            state="bull",
            transition="improving",
            strength=0.8,
            confidence=None,
            narrative="state observed but confidence is an unverified heuristic, left None",
            inputs={"raw_score": 80},
        )


class DegradedModule:
    """state=None을 산출해 degrade를 모의하는 더미 Module."""

    id = "dummy.degraded"
    tier = "dummy"

    def available_for(self, market: str) -> bool:
        return True

    def required_series(self, entity_id, ctx):
        return []

    def compute(self, entity_id, ctx, data) -> ModuleOutput:
        return ModuleOutput(
            module_id=self.id,
            state=None,
            transition=None,
            strength=None,
            confidence=None,
            narrative="data unavailable for this module",
            inputs={},
        )


class UnavailableModule:
    """available_for가 항상 False인 더미 Module — outs에서 제외되어야 한다."""

    id = "dummy.unavailable"
    tier = "dummy"

    def available_for(self, market: str) -> bool:
        return False

    def required_series(self, entity_id, ctx):
        return []

    def compute(self, entity_id, ctx, data) -> ModuleOutput:
        # available_for가 False이므로 Engine.run()이 이 메서드를 호출하지
        # 않아야 한다. 호출되면 테스트가 실패하도록 예외를 던진다.
        raise AssertionError(
            "compute()는 available_for=False인 모듈에서 호출되면 안 된다"
        )


class FirstDirectionRulebook:
    """절대 평균을 내지 않고 첫 모듈의 state를 단순 패턴 매칭하는 더미 Rulebook.

    "6축 합산 금지" 불변식 검증용 — 모듈이 여러 개여도 평균이 아니라 첫
    모듈의 state만 보고 direction을 패턴 매칭으로 결정한다.
    """

    def interpret(self, modules, upstream: Context) -> Verdict:
        if not modules:
            return Verdict(
                direction="neutral",
                strength=0,
                conviction=None,
                lead_pattern=None,
                narrative="no modules observed",
                risks=["no_data"],
                invalidation=[],
                horizon="T0",
                verified=False,
                extra={},
            )

        first = modules[0]
        # 패턴 매칭만 — 점수 합산/평균 없음.
        if first.state == "bull":
            direction = "up"
            lead_pattern = "Simple Bull Pattern"
        elif first.state is None:
            direction = "neutral"
            lead_pattern = None
        else:
            direction = "neutral"
            lead_pattern = None

        return Verdict(
            direction=direction,
            strength=2,
            conviction=0.5,
            lead_pattern=lead_pattern,
            narrative=f"pattern-matched from first module state={first.state!r}",
            risks=[],
            invalidation=[],
            horizon="T0",
            verified=False,
            extra={"module_count": len(modules)},
        )


class EngineRunTests(unittest.TestCase):
    """Engine.run()의 핵심 절차를 검증한다."""

    def test_run_returns_engine_output_with_correct_fields(self) -> None:
        engine = Engine(
            tier="dummy",
            modules=[HealthyModule()],
            rulebook=FirstDirectionRulebook(),
        )
        ctx = Context.root(market="KOSPI")

        result = engine.run("ENTITY_X", ctx, data=None)

        self.assertIsInstance(result, EngineOutput)
        self.assertEqual(result.tier, "dummy")
        self.assertEqual(result.entity_id, "ENTITY_X")
        self.assertIsInstance(result.verdict, Verdict)
        self.assertEqual(result.verdict.direction, "up")
        self.assertEqual(len(result.modules), 1)
        self.assertEqual(result.modules[0].module_id, "dummy.healthy")

    def test_unavailable_module_excluded_from_outs(self) -> None:
        engine = Engine(
            tier="dummy",
            modules=[HealthyModule(), UnavailableModule()],
            rulebook=FirstDirectionRulebook(),
        )
        ctx = Context.root(market="KOSPI")

        result = engine.run("ENTITY_X", ctx, data=None)

        # UnavailableModule.compute()가 호출됐다면 AssertionError가
        # 발생해 이 테스트 자체가 실패했을 것이다. 여기서는 outs에
        # 그 모듈의 결과가 없는지도 명시적으로 확인한다.
        module_ids = [m.module_id for m in result.modules]
        self.assertNotIn("dummy.unavailable", module_ids)
        self.assertEqual(module_ids, ["dummy.healthy"])

    def test_degraded_module_sets_mode_degraded(self) -> None:
        engine = Engine(
            tier="dummy",
            modules=[HealthyModule(), DegradedModule()],
            rulebook=FirstDirectionRulebook(),
        )
        ctx = Context.root(market="KOSPI")

        result = engine.run("ENTITY_X", ctx, data=None)

        self.assertEqual(result.mode, "degraded")

    def test_all_healthy_modules_yield_live_mode(self) -> None:
        engine = Engine(
            tier="dummy",
            modules=[HealthyModule()],
            rulebook=FirstDirectionRulebook(),
        )
        ctx = Context.root(market="KOSPI")

        result = engine.run("ENTITY_X", ctx, data=None)

        self.assertEqual(result.mode, "live")

    def test_state_present_but_confidence_none_yields_live_mode(self) -> None:
        """state는 유효하지만 confidence=None인 모듈만 있으면 mode=="live"여야
        한다 — confidence는 비검증 휴리스틱(§9.1)이라 정상적으로 None일 수
        있고(예: macro 모듈은 축별 confidence 개념이 없음), state=None이
        아닌 한 이것만으로 degraded 오판을 일으키면 안 된다(0단계 키스톤 보정
        회귀 테스트)."""
        engine = Engine(
            tier="dummy",
            modules=[StateOnlyNoConfidenceModule()],
            rulebook=FirstDirectionRulebook(),
        )
        ctx = Context.root(market="KOSPI")

        result = engine.run("ENTITY_X", ctx, data=None)

        self.assertEqual(result.mode, "live")

    def test_rulebook_does_not_average_uses_pattern_matching_only(self) -> None:
        """두 정상 모듈이 다른 state를 가져도 Rulebook이 평균 없이
        첫 모듈만 보고 패턴 매칭한다는 것을 확인한다(6축 합산 금지 검증)."""

        class BearModule(HealthyModule):
            id = "dummy.bear"

            def compute(self, entity_id, ctx, data) -> ModuleOutput:
                return ModuleOutput(
                    module_id=self.id,
                    state="bear",
                    transition="weakening",
                    strength=0.2,
                    confidence=0.6,
                    narrative="bear module",
                    inputs={},
                )

        engine = Engine(
            tier="dummy",
            modules=[HealthyModule(), BearModule()],
            rulebook=FirstDirectionRulebook(),
        )
        ctx = Context.root(market="KOSPI")

        result = engine.run("ENTITY_X", ctx, data=None)

        # 첫 모듈(state="bull")만 보고 direction="up"이 됐어야 한다 —
        # 평균이었다면 bull+bear가 섞여 다른 결과가 나왔을 것이다.
        self.assertEqual(result.verdict.direction, "up")
        self.assertEqual(result.verdict.extra["module_count"], 2)


class ContextCascadeTests(unittest.TestCase):
    """Context.root -> from_macro -> from_sector 캐스케이드 체인 보존을 검증한다."""

    def test_chain_preserves_macro_and_sector_upstream(self) -> None:
        root_ctx = Context.root(market="KOSPI")
        self.assertEqual(root_ctx.upstream, {})

        macro_verdict = Verdict(
            direction="up",
            strength=3,
            conviction=0.7,
            lead_pattern="Liquidity Expansion",
            narrative="macro bull regime",
            risks=["fed_pivot_risk"],
            invalidation=["usdkrw_breakout"],
            horizon="T2",
            verified=False,
            extra={"supportedCeiling": 3200},
        )
        macro_output = EngineOutput(
            tier="macro",
            entity_id="KOSPI",
            verdict=macro_verdict,
            modules=[],
            context=root_ctx.as_dict(),
            freshness=[],
            mode="live",
        )

        macro_ctx = Context.from_macro(macro_output)
        self.assertEqual(macro_ctx.market, "KOSPI")
        self.assertIn("macro", macro_ctx.upstream)
        self.assertEqual(macro_ctx.upstream["macro"], macro_verdict)
        self.assertNotIn("sector", macro_ctx.upstream)

        sector_verdict = Verdict(
            direction="strong_up",
            strength=4,
            conviction=0.8,
            lead_pattern="Strong Leader",
            narrative="sector leading rotation",
            risks=[],
            invalidation=[],
            horizon="T1",
            verified=False,
            extra={"quadrant": "leading"},
        )
        sector_output = EngineOutput(
            tier="sector",
            entity_id="SEC_SEMI",
            verdict=sector_verdict,
            modules=[],
            context=macro_ctx.as_dict(),
            freshness=[],
            mode="live",
        )

        sector_ctx = Context.from_sector(sector_output, base=macro_ctx)

        # 체인 보존 검증: macro와 sector가 둘 다 upstream에 남아있어야 한다.
        self.assertIn("macro", sector_ctx.upstream)
        self.assertIn("sector", sector_ctx.upstream)
        self.assertEqual(sector_ctx.upstream["macro"], macro_verdict)
        self.assertEqual(sector_ctx.upstream["sector"], sector_verdict)
        self.assertEqual(sector_ctx.market, "KOSPI")

    def test_from_sector_does_not_mutate_base_upstream(self) -> None:
        """from_sector가 base.upstream을 in-place로 변경하지 않는지 확인한다."""
        root_ctx = Context.root(market="NASDAQ")
        macro_output = EngineOutput(
            tier="macro",
            entity_id="NASDAQ",
            verdict=Verdict(
                direction="neutral",
                strength=2,
                conviction=None,
                lead_pattern=None,
                narrative="macro neutral",
                horizon="T1",
            ),
            context=root_ctx.as_dict(),
        )
        macro_ctx = Context.from_macro(macro_output)
        upstream_before = dict(macro_ctx.upstream)

        sector_output = EngineOutput(
            tier="sector",
            entity_id="SEC_TECH",
            verdict=Verdict(
                direction="up",
                strength=3,
                conviction=None,
                lead_pattern=None,
                narrative="sector up",
                horizon="T1",
            ),
            context=macro_ctx.as_dict(),
        )
        Context.from_sector(sector_output, base=macro_ctx)

        # macro_ctx.upstream은 변하지 않아야 한다(불변성).
        self.assertEqual(macro_ctx.upstream, upstream_before)
        self.assertNotIn("sector", macro_ctx.upstream)


class SerializationTests(unittest.TestCase):
    """EngineOutput/Verdict의 to_dict()가 중첩까지 직렬화되어 JSON 가능한지 검증한다."""

    def _build_sample_engine_output(self) -> EngineOutput:
        engine = Engine(
            tier="dummy",
            modules=[HealthyModule(), DegradedModule()],
            rulebook=FirstDirectionRulebook(),
        )
        ctx = Context.root(market="KOSPI")
        return engine.run("ENTITY_X", ctx, data=None)

    def test_engine_output_to_dict_is_json_serializable(self) -> None:
        result = self._build_sample_engine_output()

        as_dict = result.to_dict()

        self.assertIsInstance(as_dict, dict)
        # 중첩 검증: verdict와 modules가 dict/list[dict]로 펼쳐져 있어야 한다.
        self.assertIsInstance(as_dict["verdict"], dict)
        self.assertIsInstance(as_dict["modules"], list)
        self.assertTrue(all(isinstance(m, dict) for m in as_dict["modules"]))

        # json.dumps가 예외 없이 통과해야 한다(완전한 재귀 직렬화 검증).
        serialized = json.dumps(as_dict)
        self.assertIsInstance(serialized, str)

        round_tripped = json.loads(serialized)
        self.assertEqual(round_tripped["tier"], "dummy")
        self.assertEqual(round_tripped["entity_id"], "ENTITY_X")
        self.assertEqual(round_tripped["verdict"]["direction"], "up")

    def test_verdict_to_dict_is_json_serializable(self) -> None:
        verdict = Verdict(
            direction="strong_down",
            strength=4,
            conviction=0.9,
            lead_pattern="Breakdown",
            narrative="strong breakdown observed",
            risks=["liquidity_crunch"],
            invalidation=["regime_shift"],
            horizon="T3",
            verified=False,
            extra={"position_size_hint": 0.0},
        )

        as_dict = verdict.to_dict()
        serialized = json.dumps(as_dict)
        round_tripped = json.loads(serialized)

        self.assertEqual(round_tripped["direction"], "strong_down")
        self.assertEqual(round_tripped["horizon"], "T3")
        self.assertEqual(round_tripped["extra"]["position_size_hint"], 0.0)


if __name__ == "__main__":
    unittest.main()
