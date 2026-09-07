"""Stage-R: Advanced Medical Retrieval Intelligence Layer.
"""

from .models import (
    EvaluationResult,
    EvidenceBlock,
    EvidenceCandidate,
    EvidencePacket,
    QueryIntent,
    RerankedEvidence,
    RetrievalQuery,
    ScoreBreakdown,
)
from .query_analyzer import (
    analyze_query,
    detect_intent,
    extract_entities,
)
from .query_expansion import (
    expand_query,
    get_synonyms,
)
from .hybrid_retriever import (
    DenseRetrieverInterface,
    HybridRetriever,
    SparseBM25Retriever,
    StubDenseRetriever,
)
from .reranker import (
    MedicalReranker,
    RerankerInterface,
)
from .context_compressor import (
    ContextCompressor,
    extract_relevant_sentences,
)
from .evidence_builder import build_evidence_packet
from .evaluation import (
    compute_hit_rate,
    compute_mrr,
    compute_precision_at_k,
    compute_recall_at_k,
    evaluate_retrieval,
)
from .pipeline import StageRPipeline

__all__ = [
    # Models
    "EvaluationResult",
    "EvidenceBlock",
    "EvidenceCandidate",
    "EvidencePacket",
    "QueryIntent",
    "RerankedEvidence",
    "RetrievalQuery",
    "ScoreBreakdown",
    # Query Analysis & Expansion
    "analyze_query",
    "detect_intent",
    "extract_entities",
    "expand_query",
    "get_synonyms",
    # Hybrid Retrieval
    "DenseRetrieverInterface",
    "HybridRetriever",
    "SparseBM25Retriever",
    "StubDenseRetriever",
    # Reranking
    "MedicalReranker",
    "RerankerInterface",
    # Context Compression
    "ContextCompressor",
    "extract_relevant_sentences",
    # Evidence Builder
    "build_evidence_packet",
    # Evaluation
    "compute_hit_rate",
    "compute_mrr",
    "compute_precision_at_k",
    "compute_recall_at_k",
    "evaluate_retrieval",
    # Pipeline
    "StageRPipeline",
]
