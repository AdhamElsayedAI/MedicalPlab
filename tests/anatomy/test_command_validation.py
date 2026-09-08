import unittest

from medicalplab.anatomy.commands import AnatomyAction, AnatomyCommand
from medicalplab.anatomy.ontology import MVP_STRUCTURES, resolve_structure
from medicalplab.anatomy.validator import AnatomyCommandError, validate_anatomy_command


class TestAnatomyCommandValidation(unittest.TestCase):
    def test_mvp_contains_eleven_structures(self):
        self.assertEqual(len(MVP_STRUCTURES), 11)

    def test_alias_resolves_to_canonical_id(self):
        structure = resolve_structure("left anterior descending")
        self.assertIsNotNone(structure)
        assert structure is not None
        self.assertEqual(structure.structure_id, "lad")

    def test_valid_command_is_canonicalized(self):
        command = AnatomyCommand(
            action=AnatomyAction.HIGHLIGHT,
            structure_ids=("LAD artery", "left ventricle"),
        )
        validated = validate_anatomy_command(command)
        self.assertEqual(validated.structure_ids, ("lad", "left_ventricle"))

    def test_unknown_structure_is_rejected(self):
        command = AnatomyCommand(
            action=AnatomyAction.FOCUS,
            structure_ids=("hallucinated_coronary_branch",),
        )
        with self.assertRaises(AnatomyCommandError):
            validate_anatomy_command(command)

    def test_reset_needs_no_structure(self):
        command = AnatomyCommand(action=AnatomyAction.RESET)
        self.assertEqual(validate_anatomy_command(command), command)


if __name__ == "__main__":
    unittest.main()
