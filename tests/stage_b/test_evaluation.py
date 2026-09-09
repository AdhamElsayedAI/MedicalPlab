import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import asdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evaluation"))
from stage_b_metrics import metrics, fraction
from run_stage_b_calibration import atomic, execute, validate_resume
from medicalplab.stage_b.models import EvidenceBlock


def row(gold, pred, status="ok"):
    return dict(
        case_id=str(gold) + str(pred),
        gold_label=gold,
        prediction=pred,
        status=status,
        language="en",
        claim_type="direct_fact",
        negative_type=None,
        contrast_group_id="g",
        latency_seconds=1,
        trace=[],
    )


class FakeBackend:
    model = "fixture"
    revision = "fixture"

    def __init__(self):
        self.calls = []

    def peak_vram(self):
        return None

    def generate(self, system, user):
        self.calls.append(json.loads(user))
        if len(self.calls) % 2:
            data = {
                "claims": [
                    dict(
                        claim_id="C1",
                        text="What fact?",
                        query_span="What fact?",
                        origin="requested_fact",
                        source_document=None,
                        exact=False,
                    )
                ]
            }
        else:
            # Echo the claim text from the verifier input to match
            # post-normalization text (normalize_claim_text strips trailing "?")
            parsed_input = self.calls[-1]
            claim_text = parsed_input["claims"][0]["text"]
            data = {
                "claims": [
                    dict(
                        claim_id="C1",
                        text=claim_text,
                        status="supported",
                        citations=[{"ref": "D:B0000", "quote": "fact"}],
                        bindings=[],
                        reason="direct",
                    )
                ]
            }
        return {"text": json.dumps(data), "input_tokens": 3, "output_tokens": 4}


class Evaluation(unittest.TestCase):
    def test_atomic_serialization_failure_preserves_previous(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "checkpoint.json"
            atomic(p, {"good": True})
            with self.assertRaises(TypeError):
                atomic(p, {"bad": object()})
            self.assertEqual(json.loads(p.read_text()), {"good": True})
            self.assertEqual(len(list(Path(temp).iterdir())), 1)

    def test_backend_error_not_contract_failure(self):
        class Broken(FakeBackend):
            def generate(self, *args):
                raise ValueError("model backend failed")

        cases = [dict(case_id="x", query="What fact?", support_label="supported")]
        packet = tuple(
            EvidenceBlock(f"D:B{i:04d}", "D", "source", "", "", "fact")
            for i in range(10)
        )
        with tempfile.TemporaryDirectory() as temp:
            result = execute(
                cases, {"x": packet}, Broken(), Path(temp) / "out.json", {"rows": []}
            )
        self.assertEqual(result["metrics"]["model_failures"], 1)
        self.assertEqual(result["metrics"]["contract_failures"], 0)

    def test_gpu_preflight_without_loading_weights(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        from medicalplab.stage_b.backend import preflight

        cuda = SimpleNamespace(
            is_available=lambda: True, mem_get_info=lambda: (3 * 1024**3, 3 * 1024**3)
        )
        with patch.dict(sys.modules, {"torch": SimpleNamespace(cuda=cuda)}):
            with self.assertRaisesRegex(RuntimeError, "Need >=4 GiB"):
                preflight()

    def test_metrics_denominators(self):
        m = metrics(
            [
                row("supported", "supported"),
                row("partial", "supported"),
                row("supported", None, "contract_failure"),
                row("unsupported", "unsupported"),
            ]
        )
        self.assertEqual(m["strict_end_to_end_correctness"]["rate"], 0.5)
        self.assertEqual(m["unsafe_accept"]["count"], 1)
        self.assertEqual(m["unsafe_accept"]["denominator"], 2)
        self.assertEqual(m["contract_pass"]["rate"], 0.75)
        self.assertEqual(m["supported_accept_precision"]["rate"], 0.5)
        self.assertEqual(m["end_to_end_supported_recall"]["rate"], 0.5)

    def test_zero_denominators(self):
        self.assertIsNone(metrics([])["macro_f1"])
        self.assertIsNone(fraction(0, 0)["rate"])
        self.assertGreater(fraction(0, 28)["wilson95"][1], 0)

    def test_reversals_and_failures(self):
        m = metrics([row("supported", "unsupported"), row("unsupported", "supported")])
        self.assertEqual(m["pairwise_reversals"]["count"], 1)
        self.assertEqual(m["contrastive_group_exact"]["count"], 0)

    def test_atomic_checkpoint_and_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "out.json"
            atomic(p, {"x": 1})
            atomic(p, {"x": 2})
            self.assertEqual(json.loads(p.read_text()), {"x": 2})
            self.assertEqual(len(list(Path(temp).iterdir())), 1)
        cases = [{"case_id": "a", "support_label": "supported"}]
        saved = {
            "signature": {},
            "rows": [],
            "complete": False,
            "rows_sha256": hashlib.sha256(b"[]").hexdigest(),
        }
        validate_resume(saved, {}, cases)
        for bad in [
            dict(saved, signature={"changed": True}),
            dict(saved, complete=True),
            dict(saved, rows=[{"case_id": "b"}]),
        ]:
            with self.assertRaises(ValueError):
                validate_resume(bad, {}, cases)

    def test_end_to_end_whitelist_and_checkpoint(self):
        cases = [
            dict(
                case_id="x",
                query="What fact?",
                support_label="supported",
                supporting_blocks=["GOLD_SECRET"],
                negative_type="GOLD_SECRET",
            )
        ]
        packet = tuple(
            EvidenceBlock(f"D:B{i:04d}", "D", "source", "", "", "fact")
            for i in range(10)
        )
        backend = FakeBackend()
        with tempfile.TemporaryDirectory() as temp:
            saved = execute(
                cases, {"x": packet}, backend, Path(temp) / "out.json", {"rows": []}
            )
        self.assertEqual(saved["rows"][0]["prediction"], "supported")
        self.assertNotIn("GOLD_SECRET", json.dumps(backend.calls))
        self.assertEqual(len(backend.calls[1]["evidence"]), 10)
        self.assertEqual(saved["metrics"]["tokens"]["input_tokens"], 6)

    def test_malformed_output_continues(self):
        class Malformed(FakeBackend):
            def generate(self, *args):
                return {"text": "not JSON", "input_tokens": 1, "output_tokens": 2}

        cases = [
            dict(case_id=str(i), query="What fact?", support_label="supported")
            for i in range(2)
        ]
        packet = tuple(
            EvidenceBlock(f"D:B{i:04d}", "D", "source", "", "", "fact")
            for i in range(10)
        )
        with tempfile.TemporaryDirectory() as temp:
            result = execute(
                cases,
                {c["case_id"]: packet for c in cases},
                Malformed(),
                Path(temp) / "out.json",
                {"rows": []},
            )
        self.assertEqual(result["metrics"]["model_failures"], 2)
        self.assertTrue(result["complete"])
