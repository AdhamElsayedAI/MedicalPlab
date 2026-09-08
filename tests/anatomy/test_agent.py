import json
import unittest

from medicalplab.anatomy.agent import AnatomyAgentError, AnatomyCommandAgent
from medicalplab.anatomy.commands import AnatomyAction


class FakeBackend:
    model = "fake-anatomy-backend"

    def __init__(self, payload):
        self.payload = payload

    def generate(self, system, user):
        return {"text": json.dumps(self.payload)}


class TestAnatomyCommandAgent(unittest.TestCase):
    def test_valid_model_command_is_canonicalized(self):
        agent = AnatomyCommandAgent(
            FakeBackend(
                {
                    "action": "focus",
                    "structure_ids": ["Left Anterior Descending"],
                    "opacity": None,
                }
            )
        )
        command = agent.plan("Show me the LAD")
        self.assertEqual(command.action, AnatomyAction.FOCUS)
        self.assertEqual(command.structure_ids, ("lad",))

    def test_hallucinated_structure_is_rejected(self):
        agent = AnatomyCommandAgent(
            FakeBackend(
                {
                    "action": "focus",
                    "structure_ids": ["made_up_artery"],
                    "opacity": None,
                }
            )
        )
        with self.assertRaises(AnatomyAgentError):
            agent.plan("Show a made-up artery")

    def test_model_can_explicitly_refuse_unresolved_structure(self):
        agent = AnatomyCommandAgent(
            FakeBackend(
                {
                    "error": "structure_not_resolved",
                    "message": "No matching structure exists in the inventory",
                }
            )
        )
        with self.assertRaises(AnatomyAgentError):
            agent.plan("Show an unsupported structure")


if __name__ == "__main__":
    unittest.main()
