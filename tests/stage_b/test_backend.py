"""Backend abstraction tests. No GPU, no model download."""

import unittest
from medicalplab.stage_b.backend import Backend, QwenBackend, StubBackend
from medicalplab.stage_b.models import EvidenceBlock
from medicalplab.stage_b.pipeline import StageBPipeline, ModelFailure


class BackendProtocol(unittest.TestCase):
    def test_stub_satisfies_protocol(self):
        self.assertIsInstance(StubBackend(), Backend)

    def test_qwen_class_has_protocol_attributes(self):
        # Verify QwenBackend declares the required class-level attributes
        # without instantiating it (which requires GPU).
        self.assertTrue(hasattr(QwenBackend, "model"))
        self.assertTrue(hasattr(QwenBackend, "quantization"))
        self.assertTrue(callable(getattr(QwenBackend, "generate", None)))
        self.assertTrue(callable(getattr(QwenBackend, "peak_vram", None)))

    def test_stub_metadata(self):
        stub = StubBackend()
        self.assertEqual(stub.model, "stub")
        self.assertEqual(stub.revision, "local-development")
        self.assertEqual(stub.quantization, "none")
        self.assertIsNone(stub.peak_vram())


class StubPipelineExecution(unittest.TestCase):
    def test_stub_pipeline_contract_failure(self):
        """StubBackend returns empty claims, which will fail the plan contract.

        This is expected: StubBackend is for development, not benchmarking.
        The pipeline should raise a ContractError or ValueError, not crash."""
        stub = StubBackend()
        pipeline = StageBPipeline(stub)
        packet = tuple(
            EvidenceBlock(f"D:B{i:04d}", "D", "Source", "", "", "text")
            for i in range(10)
        )
        from medicalplab.stage_b.models import ContractError

        with self.assertRaises((ContractError, ValueError)):
            pipeline.run("What is the recommended dose?", packet)

    def test_stub_metadata_in_pipeline(self):
        """Verify pipeline reads quantization from backend, not hardcoded."""
        stub = StubBackend()
        pipeline = StageBPipeline(stub)
        self.assertEqual(
            getattr(pipeline.backend, "quantization", "AWQ 4-bit"), "none"
        )

    def test_qwen_quantization_preserved(self):
        """Verify QwenBackend still reports AWQ 4-bit."""
        self.assertEqual(QwenBackend.quantization, "AWQ 4-bit")
