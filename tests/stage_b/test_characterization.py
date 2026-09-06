import json, unittest
from pathlib import Path
from .fixtures.legacy_validator import local_validate


class EmptySchema:
    def iter_errors(self, output):
        return iter(())


class Characterization(unittest.TestCase):
    def test_all_required_cases_preserved(self):
        fixtures = json.loads(
            (Path(__file__).parent / "fixtures/characterization.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            [int(r["case"]["case_id"].split("-")[-1]) for r in fixtures],
            [2, 11, 12, 26, 27, 29, 32, 35, 41, 42, 43, 48],
        )
        for row in fixtures:
            with self.subTest(case=row["case"]["case_id"]):
                self.assertEqual(len(row["retrieval"]["top_10_blocks"]), 10)
                self.assertEqual(len(set(row["retrieval"]["top_10_blocks"])), 10)
                self.assertIn(
                    row["case"]["support_label"],
                    ["supported", "partial", "unsupported"],
                )

    def test_legacy_reference_restriction(self):
        self.assertTrue(
            local_validate(
                {"claims": [{"evidence_refs": ["outside"]}]}, EmptySchema(), {"inside"}
            )
        )

    def test_legacy_semantic_gap(self):
        # Characterizes only the old extra validation, independently of JSON Schema.
        # It never checked quotes or relations; this is not a desired contract.
        output = {"claims": [{"evidence_refs": ["inside"], "quote": "invented"}]}
        self.assertEqual(local_validate(output, EmptySchema(), {"inside"}), [])


def make_case_test(fixture):
    def check(self):
        root = Path(__file__).resolve().parents[2]
        calibration = json.loads(
            (root / "evaluation/evidence_sufficiency_calibration_v1.json").read_text(
                encoding="utf-8"
            )
        )
        case = next(
            c
            for c in calibration["cases"]
            if c["case_id"] == fixture["case"]["case_id"]
        )
        self.assertEqual(case, fixture["case"])
        baseline = json.loads(
            (
                root
                / "evaluation/results/evidence_sufficiency_retrieval_only_baseline_v1.json"
            ).read_text(encoding="utf-8")
        )
        actual = next(r for r in baseline["cases"] if r["case_id"] == case["case_id"])
        self.assertEqual(actual, fixture["retrieval"])
        old = fixture["historical_gemini"]
        if old is not None:
            self.assertEqual(old["case_id"], case["case_id"])
            self.assertEqual(old["gold_label"], case["support_label"])
            if old["status"] == "ok":
                self.assertEqual(
                    local_validate(
                        old["model_output"], EmptySchema(), set(actual["top_10_blocks"])
                    ),
                    [],
                )

    return check


for fixture in json.loads(
    (Path(__file__).parent / "fixtures/characterization.json").read_text(
        encoding="utf-8"
    )
):
    setattr(
        Characterization,
        "test_snapshot_" + fixture["case"]["case_id"].replace("-", "_"),
        make_case_test(fixture),
    )
