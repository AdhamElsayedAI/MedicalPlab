"""Tests for Qwen3DenseRetriever in Stage-R."""

import pytest
from medicalplab.stage_r.models import EvidenceBlock, QueryIntent, RetrievalQuery
from medicalplab.stage_r.hybrid_retriever import DenseRetrieverInterface, StubDenseRetriever
from medicalplab.stage_r.qwen3_dense_retriever import Qwen3DenseRetriever


def test_qwen3_dense_retriever_interface():
    retriever = Qwen3DenseRetriever(model_name="nonexistent-model-test", fallback_to_stub=True)
    assert isinstance(retriever, DenseRetrieverInterface)


def test_qwen3_dense_formatting():
    retriever = Qwen3DenseRetriever(fallback_to_stub=True)
    
    block = EvidenceBlock(
        ref="DOC-TEST:B0001",
        document_id="DOC-TEST",
        source="clinical_guideline",
        heading="Pharmacotherapy",
        section="2.1",
        text="Initiate monotherapy with ACE inhibitor or ARB for Stage 1 hypertension.",
    )
    formatted = retriever.format_passage(block)
    assert "Heading: Pharmacotherapy" in formatted
    assert "Section: 2.1" in formatted
    assert "Initiate monotherapy" in formatted

    query = RetrievalQuery(
        raw_query="Treatment for hypertension",
        normalized_query="treatment for hypertension",
        expanded_terms=("high blood pressure",),
        intent=QueryIntent.TREATMENT,
        entities=("hypertension",),
    )
    formatted_q = retriever.format_query(query)
    assert "Treatment for hypertension" in formatted_q
    assert "Instruct:" in formatted_q


def test_qwen3_dense_empty_corpus():
    retriever = Qwen3DenseRetriever(fallback_to_stub=True)
    query = RetrievalQuery(
        raw_query="Test query",
        normalized_query="test query",
        expanded_terms=(),
        intent=QueryIntent.EDUCATIONAL,
        entities=(),
    )
    scores = retriever.retrieve_dense(query, ())
    assert scores == {}


def test_qwen3_dense_fallback_execution():
    retriever = Qwen3DenseRetriever(model_name="mock-nonexistent-weights", fallback_to_stub=True)
    query = RetrievalQuery(
        raw_query="hypertension treatment",
        normalized_query="hypertension treatment",
        expanded_terms=(),
        intent=QueryIntent.TREATMENT,
        entities=("hypertension",),
    )
    corpus = (
        EvidenceBlock(
            ref="DOC-1:B0001",
            document_id="DOC-1",
            source="guideline",
            heading="Hypertension Treatment",
            section="1",
            text="First line treatment of hypertension includes ACE inhibitors.",
        ),
        EvidenceBlock(
            ref="DOC-1:B0002",
            document_id="DOC-1",
            source="guideline",
            heading="Pneumonia Diagnosis",
            section="2",
            text="Chest radiograph confirms consolidation in pneumonia.",
        ),
    )
    scores = retriever.retrieve_dense(query, corpus)
    assert "DOC-1:B0001" in scores
    assert "DOC-1:B0002" in scores
    # Fallback to stub gives higher score to hypertension block
    assert scores["DOC-1:B0001"] > scores["DOC-1:B0002"]
    for s in scores.values():
        assert 0.0 <= s <= 1.0
