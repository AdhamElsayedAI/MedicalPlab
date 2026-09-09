"""Unit tests for deterministic natural-language Anatomy Agent and ontology resolution."""

import unittest

from medicalplab.anatomy.agent import AnatomyAgentError, AnatomyCommandAgent, resolve_query_to_command
from medicalplab.anatomy.commands import AnatomyAction
from medicalplab.anatomy.provider import ASTRA_ORGAN_MODEL, StaticCardiovascularAssetProvider


class TestAnatomyDeterministicAgent(unittest.TestCase):
    def test_canonical_structure_resolution(self):
        cmd, ctx = resolve_query_to_command("Show me the left ventricle")
        self.assertEqual(cmd.action, AnatomyAction.SHOW)
        self.assertEqual(cmd.structure_ids, ("left_ventricle",))
        self.assertEqual(ctx.get("structure_id"), "left_ventricle")

    def test_approved_alias_resolution(self):
        cmd, _ = resolve_query_to_command("Highlight the LAD artery")
        self.assertEqual(cmd.action, AnatomyAction.HIGHLIGHT)
        self.assertEqual(cmd.structure_ids, ("lad",))

    def test_bicuspid_valve_alias(self):
        cmd, _ = resolve_query_to_command("Focus on the bicuspid valve")
        self.assertEqual(cmd.action, AnatomyAction.FOCUS)
        self.assertEqual(cmd.structure_ids, ("mitral_valve",))

    def test_reset_command(self):
        cmd, ctx = resolve_query_to_command("Reset the viewport view")
        self.assertEqual(cmd.action, AnatomyAction.RESET)
        self.assertEqual(cmd.structure_ids, ())
        self.assertEqual(ctx.get("action"), "reset")

    def test_unsupported_organ_refusal(self):
        with self.assertRaises(AnatomyAgentError) as ctx:
            resolve_query_to_command("Show me the kidney")
        self.assertIn("UNSUPPORTED_STRUCTURE", str(ctx.exception))

    def test_unsupported_brain_refusal(self):
        with self.assertRaises(AnatomyAgentError) as ctx:
            resolve_query_to_command("Highlight the brain")
        self.assertIn("UNSUPPORTED_STRUCTURE", str(ctx.exception))

    def test_invalid_query_refusal(self):
        with self.assertRaises(AnatomyAgentError):
            resolve_query_to_command("Make it blue")

    def test_empty_query_refusal(self):
        with self.assertRaises(AnatomyAgentError):
            resolve_query_to_command("   ")

    def test_agent_plan_without_backend_uses_deterministic_resolver(self):
        agent = AnatomyCommandAgent(backend=None)
        cmd = agent.plan("Focus on aorta")
        self.assertEqual(cmd.action, AnatomyAction.FOCUS)
        self.assertEqual(cmd.structure_ids, ("aorta",))
        self.assertEqual(len(agent.trace), 1)

    def test_astra_organ_model_flag_and_provider(self):
        self.assertEqual(ASTRA_ORGAN_MODEL, "NOT VERIFIED")
        provider = StaticCardiovascularAssetProvider()
        assets = provider.list_available_assets()
        self.assertEqual(len(assets), 11)
        desc = provider.get_asset_descriptor("left_ventricle")
        self.assertIsNotNone(desc)
        assert desc is not None
        self.assertEqual(desc.structure_id, "left_ventricle")


if __name__ == "__main__":
    unittest.main()
