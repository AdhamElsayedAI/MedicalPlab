"""Tests for Stage-R runtime-mode guardrails and strict fail-closed behavior."""

import os
import pytest
from unittest.mock import patch

from medicalplab.stage_g.runtime import RuntimeMode, _ENV_NAME
from medicalplab.stage_r.hybrid_retriever import HybridRetriever, StubDenseRetriever
from medicalplab.stage_r.pipeline import StageRPipeline
from medicalplab.stage_r.qwen3_dense_retriever import Qwen3DenseRetriever


def test_demo_mode_allows_stub_retriever():
    with patch.dict(os.environ, {_ENV_NAME: "demo"}):
        retriever = HybridRetriever(alpha=0.5)
        assert isinstance(retriever.dense_retriever, StubDenseRetriever)

        pipeline = StageRPipeline(alpha=0.5)
        assert isinstance(pipeline.retriever.dense_retriever, StubDenseRetriever)


def test_test_mode_allows_stub_retriever():
    with patch.dict(os.environ, {_ENV_NAME: "test"}):
        retriever = HybridRetriever(alpha=0.5)
        assert isinstance(retriever.dense_retriever, StubDenseRetriever)


def test_pilot_mode_forbids_stub_dense_retriever():
    with patch.dict(os.environ, {_ENV_NAME: "pilot"}):
        # Implicit dense_retriever=None must raise ValueError
        with pytest.raises(ValueError, match="dense_retriever must be explicitly provided"):
            HybridRetriever(alpha=0.5)

        # Explicit StubDenseRetriever must raise ValueError
        with pytest.raises(ValueError, match="StubDenseRetriever cannot be used in strict runtime mode"):
            HybridRetriever(dense_retriever=StubDenseRetriever(), alpha=0.5)


def test_production_mode_forbids_stub_dense_retriever():
    with patch.dict(os.environ, {_ENV_NAME: "production"}):
        with pytest.raises(ValueError, match="dense_retriever must be explicitly provided"):
            HybridRetriever(alpha=0.5)

        with pytest.raises(ValueError, match="StubDenseRetriever cannot be used in strict runtime mode"):
            HybridRetriever(dense_retriever=StubDenseRetriever(), alpha=0.5)


def test_qwen3_dense_retriever_fails_closed_in_strict_mode():
    with patch.dict(os.environ, {_ENV_NAME: "production"}):
        # Explicit fallback_to_stub=True is forbidden
        with pytest.raises(ValueError, match="fallback_to_stub=True is forbidden in strict runtime mode"):
            Qwen3DenseRetriever(fallback_to_stub=True)

        # Non-existent model must fail closed (RuntimeError) instead of falling back to stub
        retriever = Qwen3DenseRetriever(model_name="nonexistent-weights-path-fail")
        assert retriever.fallback_to_stub is False
        with pytest.raises(RuntimeError, match="Fail closed"):
            retriever._get_model()
