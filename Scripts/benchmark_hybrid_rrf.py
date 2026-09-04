import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHUNKS_PATH = (
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
    / "DOC-WHO-CARD-0001.chunks.json"
)

EVAL_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_eval_v1.json"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "evaluation"
    / "results"
)


# ============================================================
# Retrieval configuration
# ============================================================

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

TOP_K_VALUES = (1, 3, 5, 10)

RRF_K = 60

DENSE_WEIGHT = 2.0
BM25_WEIGHT = 1.0

CANDIDATES_PER_RETRIEVER = 30

QUERY_INSTRUCTION = (
    "Instruct: Given a medical education query, retrieve authoritative "
    "clinical guideline passages that directly answer the question. "
    "Prioritize recommendations, implementation remarks, and supporting "
    "evidence.\nQuery:"
)


# ============================================================
# JSON
# ============================================================

def load_json(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


# ============================================================
# BM25
# ============================================================

def tokenize(
    text: str,
) -> list[str]:
    text = text.lower()

    return re.findall(
        r"[a-z0-9]+|[\u0600-\u06ff]+",
        text,
    )


class BM25:
    def __init__(
        self,
        documents: list[list[str]],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if not documents:
            raise ValueError(
                "BM25 requires at least one document."
            )

        self.documents = documents
        self.k1 = k1
        self.b = b

        self.doc_count = len(
            documents
        )

        self.doc_lengths = [
            len(document)
            for document in documents
        ]

        self.average_doc_length = (
            sum(self.doc_lengths)
            / self.doc_count
        )

        self.term_frequencies = [
            Counter(document)
            for document in documents
        ]

        document_frequency: Counter[str] = Counter()

        for document in documents:
            for token in set(document):
                document_frequency[token] += 1

        self.idf: dict[str, float] = {}

        for token, frequency in document_frequency.items():
            self.idf[token] = math.log(
                1.0
                + (
                    self.doc_count
                    - frequency
                    + 0.5
                )
                / (
                    frequency
                    + 0.5
                )
            )

    def score(
        self,
        query_tokens: list[str],
        document_index: int,
    ) -> float:
        frequencies = self.term_frequencies[
            document_index
        ]

        document_length = self.doc_lengths[
            document_index
        ]

        score = 0.0

        for token in query_tokens:
            term_frequency = frequencies.get(
                token,
                0,
            )

            if term_frequency == 0:
                continue

            idf = self.idf.get(
                token,
                0.0,
            )

            denominator = (
                term_frequency
                + self.k1
                * (
                    1.0
                    - self.b
                    + self.b
                    * document_length
                    / max(
                        self.average_doc_length,
                        1.0,
                    )
                )
            )

            score += (
                idf
                * term_frequency
                * (
                    self.k1
                    + 1.0
                )
                / denominator
            )

        return score

    def get_scores(
        self,
        query_tokens: list[str],
    ) -> list[float]:
        return [
            self.score(
                query_tokens,
                document_index,
            )
            for document_index in range(
                self.doc_count
            )
        ]


# ============================================================
# Retrieval text
# ============================================================

def section_path_to_text(
    section_path: Any,
) -> str:
    if isinstance(
        section_path,
        list,
    ):
        return " > ".join(
            str(item)
            for item in section_path
        )

    if section_path is None:
        return ""

    return str(
        section_path
    )


def topics_to_text(
    topics: Any,
) -> str:
    if isinstance(
        topics,
        list,
    ):
        return ", ".join(
            str(item)
            for item in topics
        )

    if topics is None:
        return ""

    return str(
        topics
    )


def build_bm25_text(
    chunk: dict[str, Any],
) -> str:
    parts = [
        str(
            chunk.get(
                "medical_specialty",
                "",
            )
        ),
        str(
            chunk.get(
                "heading",
                "",
            )
        ),
        section_path_to_text(
            chunk.get(
                "section_path",
                [],
            )
        ),
        str(
            chunk.get(
                "block_type",
                "",
            )
        ),
        str(
            chunk.get(
                "text",
                "",
            )
        ),
    ]

    return " ".join(
        part
        for part in parts
        if part.strip()
    )
def build_dense_text(
    chunk: dict[str, Any],
) -> str:
    parts = [
        (
            "Medical specialty: "
            + str(
                chunk.get(
                    "medical_specialty",
                    "",
                )
            )
        ),
        (
            "Topics: "
            + topics_to_text(
                chunk.get(
                    "topics",
                    [],
                )
            )
        ),
        (
            "Section: "
            + section_path_to_text(
                chunk.get(
                    "section_path",
                    [],
                )
            )
        ),
        (
            "Heading: "
            + str(
                chunk.get(
                    "heading",
                    "",
                )
            )
        ),
        (
            "Evidence type: "
            + str(
                chunk.get(
                    "block_type",
                    "",
                )
            )
        ),
        (
            "Content: "
            + str(
                chunk.get(
                    "text",
                    "",
                )
            )
        ),
    ]

    return "\n".join(
        part
        for part in parts
        if part.strip()
    )
# ============================================================
# Ranking
# ============================================================

def rank_unique_blocks(
    chunks: list[dict[str, Any]],
    scores: list[float] | np.ndarray,
    positive_only: bool = False,
) -> list[int]:
    if len(chunks) != len(scores):
        raise ValueError(
            "Chunks and scores length mismatch."
        )

    best_score_by_block: dict[
        int,
        float,
    ] = defaultdict(
        lambda: float("-inf")
    )

    for chunk, score in zip(
        chunks,
        scores,
    ):
        block_index = int(
            chunk[
                "source_block_index"
            ]
        )

        score_value = float(
            score
        )

        if (
            score_value
            > best_score_by_block[
                block_index
            ]
        ):
            best_score_by_block[
                block_index
            ] = score_value

    ranked_items = list(
        best_score_by_block.items()
    )

    if positive_only:
        ranked_items = [
            item
            for item in ranked_items
            if item[1] > 0.0
        ]

    ranked_items.sort(
        key=lambda item: (
            -item[1],
            item[0],
        )
    )

    return [
        block_index
        for block_index, _
        in ranked_items
    ]


# ============================================================
# Weighted Reciprocal Rank Fusion
# ============================================================

def weighted_rrf(
    dense_ranking: list[int],
    sparse_ranking: list[int],
    rrf_k: int,
    dense_weight: float,
    sparse_weight: float,
) -> tuple[
    list[int],
    dict[int, float],
]:
    scores: dict[
        int,
        float,
    ] = defaultdict(float)

    dense_rank_map = {
        block_index: rank
        for rank, block_index in enumerate(
            dense_ranking,
            start=1,
        )
    }

    sparse_rank_map = {
        block_index: rank
        for rank, block_index in enumerate(
            sparse_ranking,
            start=1,
        )
    }

    for rank, block_index in enumerate(
        dense_ranking,
        start=1,
    ):
        scores[
            block_index
        ] += (
            dense_weight
            / (
                rrf_k
                + rank
            )
        )

    for rank, block_index in enumerate(
        sparse_ranking,
        start=1,
    ):
        scores[
            block_index
        ] += (
            sparse_weight
            / (
                rrf_k
                + rank
            )
        )

    fused_items = sorted(
        scores.items(),
        key=lambda item: (
            -item[1],
            dense_rank_map.get(
                item[0],
                10**9,
            ),
            sparse_rank_map.get(
                item[0],
                10**9,
            ),
            item[0],
        ),
    )

    fused_ranking = [
        block_index
        for block_index, _
        in fused_items
    ]

    return (
        fused_ranking,
        dict(scores),
    )


# ============================================================
# Metrics
# ============================================================

def reciprocal_rank(
    ranked_blocks: list[int],
    relevant_blocks: set[int],
) -> float:
    for rank, block_index in enumerate(
        ranked_blocks,
        start=1,
    ):
        if block_index in relevant_blocks:
            return 1.0 / rank

    return 0.0


def hit_at_k(
    ranked_blocks: list[int],
    relevant_blocks: set[int],
    k: int,
) -> float:
    return float(
        any(
            block_index in relevant_blocks
            for block_index in ranked_blocks[:k]
        )
    )


def recall_at_k(
    ranked_blocks: list[int],
    relevant_blocks: set[int],
    k: int,
) -> float:
    if not relevant_blocks:
        return 0.0

    retrieved = set(
        ranked_blocks[:k]
    )

    return (
        len(
            retrieved
            & relevant_blocks
        )
        / len(
            relevant_blocks
        )
    )


def dcg_at_k(
    ranked_blocks: list[int],
    relevance_map: dict[int, int],
    k: int,
) -> float:
    score = 0.0

    for rank, block_index in enumerate(
        ranked_blocks[:k],
        start=1,
    ):
        relevance = relevance_map.get(
            block_index,
            0,
        )

        if relevance <= 0:
            continue

        gain = (
            (2 ** relevance)
            - 1
        )

        discount = math.log2(
            rank + 1
        )

        score += (
            gain
            / discount
        )

    return score


def ndcg_at_k(
    ranked_blocks: list[int],
    relevance_map: dict[int, int],
    k: int,
) -> float:
    actual_dcg = dcg_at_k(
        ranked_blocks,
        relevance_map,
        k,
    )

    ideal_relevances = sorted(
        relevance_map.values(),
        reverse=True,
    )

    ideal_dcg = 0.0

    for rank, relevance in enumerate(
        ideal_relevances[:k],
        start=1,
    ):
        gain = (
            (2 ** relevance)
            - 1
        )

        discount = math.log2(
            rank + 1
        )

        ideal_dcg += (
            gain
            / discount
        )

    if ideal_dcg == 0.0:
        return 0.0

    return (
        actual_dcg
        / ideal_dcg
    )


def mean(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return (
        sum(values)
        / len(values)
    )


# ============================================================
# Metric containers
# ============================================================

def create_metric_store() -> dict[str, Any]:
    return {
        "hits": {
            k: []
            for k in TOP_K_VALUES
        },
        "recalls": {
            k: []
            for k in TOP_K_VALUES
        },
        "reciprocal_ranks": [],
        "ndcg_scores": [],
    }


def update_metric_store(
    store: dict[str, Any],
    ranked_blocks: list[int],
    relevant_blocks: set[int],
    relevance_map: dict[int, int],
) -> dict[str, float]:
    query_metrics: dict[
        str,
        float,
    ] = {}

    rr = reciprocal_rank(
        ranked_blocks,
        relevant_blocks,
    )

    ndcg = ndcg_at_k(
        ranked_blocks,
        relevance_map,
        10,
    )

    store[
        "reciprocal_ranks"
    ].append(
        rr
    )

    store[
        "ndcg_scores"
    ].append(
        ndcg
    )

    query_metrics[
        "reciprocal_rank"
    ] = rr

    query_metrics[
        "ndcg_at_10"
    ] = ndcg

    for k in TOP_K_VALUES:
        hit = hit_at_k(
            ranked_blocks,
            relevant_blocks,
            k,
        )

        recall = recall_at_k(
            ranked_blocks,
            relevant_blocks,
            k,
        )

        store[
            "hits"
        ][k].append(
            hit
        )

        store[
            "recalls"
        ][k].append(
            recall
        )

        query_metrics[
            f"hit_at_{k}"
        ] = hit

        query_metrics[
            f"recall_at_{k}"
        ] = recall

    return query_metrics


def aggregate_metrics(
    store: dict[str, Any],
) -> dict[str, float]:
    aggregate: dict[
        str,
        float,
    ] = {}

    for k in TOP_K_VALUES:
        aggregate[
            f"hit_at_{k}"
        ] = mean(
            store[
                "hits"
            ][k]
        )

        aggregate[
            f"recall_at_{k}"
        ] = mean(
            store[
                "recalls"
            ][k]
        )

    aggregate["mrr"] = mean(
        store[
            "reciprocal_ranks"
        ]
    )

    aggregate[
        "ndcg_at_10"
    ] = mean(
        store[
            "ndcg_scores"
        ]
    )

    return aggregate


# ============================================================
# Main benchmark
# ============================================================

def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available."
        )

    torch.cuda.reset_peak_memory_stats()

    # --------------------------------------------------------
    # Load corpus + evaluation set
    # --------------------------------------------------------

    chunks_document = load_json(
        CHUNKS_PATH
    )

    evaluation = load_json(
        EVAL_PATH
    )

    chunks = chunks_document.get(
        "chunks",
        [],
    )

    cases = evaluation.get(
        "cases",
        [],
    )

    if not isinstance(
        chunks,
        list,
    ):
        raise ValueError(
            "chunks must be a list."
        )

    if not isinstance(
        cases,
        list,
    ):
        raise ValueError(
            "cases must be a list."
        )

    if not chunks:
        raise ValueError(
            "No chunks found."
        )

    answerable_cases = [
        case
        for case in cases
        if case.get(
            "expected_answerable"
        )
    ]

    if not answerable_cases:
        raise ValueError(
            "No answerable evaluation cases found."
        )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    print(
        "\nMedicalPlab Weighted Hybrid Retrieval Benchmark"
    )
    print("=" * 78)

    print(
        f"Dense model             : "
        f"{MODEL_NAME}"
    )

    print(
        "Sparse retriever        : BM25"
    )

    print(
        f"Fusion                  : "
        f"Weighted RRF(k={RRF_K})"
    )

    print(
        f"Dense weight            : "
        f"{DENSE_WEIGHT}"
    )

    print(
        f"BM25 weight             : "
        f"{BM25_WEIGHT}"
    )

    print(
        f"Candidates/retriever    : "
        f"{CANDIDATES_PER_RETRIEVER}"
    )

    print(
        f"Chunks                  : "
        f"{len(chunks)}"
    )

    print(
        f"Answerable queries      : "
        f"{len(answerable_cases)}"
    )

    print(
        f"GPU                     : "
        f"{torch.cuda.get_device_name(0)}"
    )

    # --------------------------------------------------------
    # BM25 index
    # --------------------------------------------------------

    bm25_documents = [
        build_bm25_text(
            chunk
        )
        for chunk in chunks
    ]

    tokenized_documents = [
        tokenize(
            text
        )
        for text in bm25_documents
    ]

    bm25 = BM25(
        tokenized_documents
    )

    # --------------------------------------------------------
    # Dense model
    # --------------------------------------------------------

    print(
        "\nLoading dense model..."
    )

    load_start = time.perf_counter()

    model = SentenceTransformer(
        MODEL_NAME,
        device="cuda",
        model_kwargs={
            "torch_dtype": torch.float16,
        },
        processor_kwargs={
            "padding_side": "left",
        },
    )

    model.max_seq_length = 2048

    load_time = (
        time.perf_counter()
        - load_start
    )

    print(
        f"Model loaded            : "
        f"{load_time:.2f}s"
    )

    # --------------------------------------------------------
    # Dense corpus embeddings
    # --------------------------------------------------------

    dense_documents = [
        build_dense_text(
            chunk
        )
        for chunk in chunks
    ]

    print(
        "Encoding corpus..."
    )

    corpus_start = time.perf_counter()

    document_embeddings = model.encode(
        dense_documents,
        batch_size=4,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    corpus_time = (
        time.perf_counter()
        - corpus_start
    )

    print(
        f"Corpus encoded          : "
        f"{corpus_time:.2f}s"
    )

    print(
        f"Embedding dimension     : "
        f"{document_embeddings.shape[1]}"
    )

    # --------------------------------------------------------
    # Query embeddings
    # --------------------------------------------------------

    queries = [
        case["query"]
        for case in answerable_cases
    ]

    query_start = time.perf_counter()

    query_embeddings = model.encode(
        queries,
        prompt=QUERY_INSTRUCTION,
        batch_size=4,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    query_time = (
        time.perf_counter()
        - query_start
    )

    print(
        f"Queries encoded         : "
        f"{query_time:.2f}s"
    )

    similarity_matrix = (
        query_embeddings
        @ document_embeddings.T
    )

    # --------------------------------------------------------
    # Metric stores
    # --------------------------------------------------------

    bm25_store = create_metric_store()
    dense_store = create_metric_store()
    hybrid_store = create_metric_store()

    per_query_results: list[
        dict[str, Any]
    ] = []

    print(
        "\nPer-query results"
    )
    print("-" * 140)

    # --------------------------------------------------------
    # Benchmark every query
    # --------------------------------------------------------

    for query_index, case in enumerate(
        answerable_cases
    ):
        query = case[
            "query"
        ]

        # Dense
        dense_scores = similarity_matrix[
            query_index
        ]

        dense_ranking = rank_unique_blocks(
            chunks,
            dense_scores,
        )

        dense_candidates = (
            dense_ranking[
                :CANDIDATES_PER_RETRIEVER
            ]
        )

        # BM25
        bm25_scores = bm25.get_scores(
            tokenize(
                query
            )
        )

        # Important:
        # Ignore zero-score blocks so an Arabic query
        # with no English lexical overlap does not
        # receive arbitrary BM25 rankings.
        bm25_ranking = rank_unique_blocks(
            chunks,
            bm25_scores,
            positive_only=True,
        )

        bm25_candidates = (
            bm25_ranking[
                :CANDIDATES_PER_RETRIEVER
            ]
        )

        # Weighted RRF
        hybrid_ranking, fusion_scores = weighted_rrf(
            dense_ranking=dense_candidates,
            sparse_ranking=bm25_candidates,
            rrf_k=RRF_K,
            dense_weight=DENSE_WEIGHT,
            sparse_weight=BM25_WEIGHT,
        )

        # Gold labels
        relevance_map = {
            item[
                "block_index"
            ]: item[
                "relevance"
            ]
            for item in case[
                "relevant_blocks"
            ]
        }

        relevant_blocks = set(
            relevance_map
        )

        # Metrics
        bm25_metrics = update_metric_store(
            bm25_store,
            bm25_ranking,
            relevant_blocks,
            relevance_map,
        )

        dense_metrics = update_metric_store(
            dense_store,
            dense_ranking,
            relevant_blocks,
            relevance_map,
        )

        hybrid_metrics = update_metric_store(
            hybrid_store,
            hybrid_ranking,
            relevant_blocks,
            relevance_map,
        )

        # Console
        print(
            f"{case['query_id']:<9} | "
            f"{case['language']:<5} | "
            f"Hybrid RR="
            f"{hybrid_metrics['reciprocal_rank']:.3f} | "
            f"nDCG@10="
            f"{hybrid_metrics['ndcg_at_10']:.3f} | "
            f"BM25={bm25_candidates[:3]} | "
            f"Dense={dense_candidates[:3]} | "
            f"Hybrid={hybrid_ranking[:5]}"
        )

        # Save per-query result
        per_query_results.append(
            {
                "query_id": (
                    case[
                        "query_id"
                    ]
                ),
                "language": (
                    case[
                        "language"
                    ]
                ),
                "query_type": (
                    case[
                        "query_type"
                    ]
                ),
                "query": query,
                "gold_blocks": (
                    sorted(
                        relevant_blocks
                    )
                ),
                "bm25_top_10": (
                    bm25_ranking[:10]
                ),
                "dense_top_10": (
                    dense_ranking[:10]
                ),
                "hybrid_top_10": (
                    hybrid_ranking[:10]
                ),
                "bm25_metrics": (
                    bm25_metrics
                ),
                "dense_metrics": (
                    dense_metrics
                ),
                "hybrid_metrics": (
                    hybrid_metrics
                ),
                "hybrid_fusion_scores_top_10": {
                    str(block_index): (
                        fusion_scores[
                            block_index
                        ]
                    )
                    for block_index
                    in hybrid_ranking[:10]
                },
            }
        )

    # --------------------------------------------------------
    # Aggregate
    # --------------------------------------------------------

    bm25_aggregate = aggregate_metrics(
        bm25_store
    )

    dense_aggregate = aggregate_metrics(
        dense_store
    )

    hybrid_aggregate = aggregate_metrics(
        hybrid_store
    )

    print(
        "\nAggregate Hybrid Metrics"
    )
    print("-" * 78)

    for k in TOP_K_VALUES:
        print(
            f"Hit@{k:<2}       : "
            f"{hybrid_aggregate[f'hit_at_{k}']:.4f}"
        )

        print(
            f"Recall@{k:<2}    : "
            f"{hybrid_aggregate[f'recall_at_{k}']:.4f}"
        )

    print(
        f"MRR          : "
        f"{hybrid_aggregate['mrr']:.4f}"
    )

    print(
        f"nDCG@10      : "
        f"{hybrid_aggregate['ndcg_at_10']:.4f}"
    )

    # --------------------------------------------------------
    # Comparison
    # --------------------------------------------------------

    print(
        "\nComparison"
    )
    print("-" * 78)

    print(
        "Metric       BM25       Dense      Weighted Hybrid"
    )

    print(
        f"Hit@1        "
        f"{bm25_aggregate['hit_at_1']:.4f}     "
        f"{dense_aggregate['hit_at_1']:.4f}     "
        f"{hybrid_aggregate['hit_at_1']:.4f}"
    )

    print(
        f"Recall@3     "
        f"{bm25_aggregate['recall_at_3']:.4f}     "
        f"{dense_aggregate['recall_at_3']:.4f}     "
        f"{hybrid_aggregate['recall_at_3']:.4f}"
    )

    print(
        f"Recall@5     "
        f"{bm25_aggregate['recall_at_5']:.4f}     "
        f"{dense_aggregate['recall_at_5']:.4f}     "
        f"{hybrid_aggregate['recall_at_5']:.4f}"
    )

    print(
        f"Recall@10    "
        f"{bm25_aggregate['recall_at_10']:.4f}     "
        f"{dense_aggregate['recall_at_10']:.4f}     "
        f"{hybrid_aggregate['recall_at_10']:.4f}"
    )

    print(
        f"MRR          "
        f"{bm25_aggregate['mrr']:.4f}     "
        f"{dense_aggregate['mrr']:.4f}     "
        f"{hybrid_aggregate['mrr']:.4f}"
    )

    print(
        f"nDCG@10      "
        f"{bm25_aggregate['ndcg_at_10']:.4f}     "
        f"{dense_aggregate['ndcg_at_10']:.4f}     "
        f"{hybrid_aggregate['ndcg_at_10']:.4f}"
    )

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------

    peak_vram = (
        torch.cuda.max_memory_allocated()
        / 1024**3
    )

    print(
        f"\nPeak CUDA memory        : "
        f"{peak_vram:.2f} GB"
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_path = (
        RESULTS_DIR
        / "hybrid_qwen06_bm25_weighted_rrf_v2.json"
    )

    payload = {
        "benchmark": (
            "MedicalPlab weighted hybrid retrieval v2"
        ),
        "dense_model": MODEL_NAME,
        "sparse_model": "BM25",
        "device": "cuda",
        "dtype": "float16",
        "embedding_dimension": int(
            document_embeddings.shape[1]
        ),
        "query_instruction": (
            QUERY_INSTRUCTION
        ),
        "fusion": {
            "strategy": (
                "weighted_reciprocal_rank_fusion"
            ),
            "rrf_k": RRF_K,
            "dense_weight": DENSE_WEIGHT,
            "bm25_weight": BM25_WEIGHT,
            "candidates_per_retriever": (
                CANDIDATES_PER_RETRIEVER
            ),
            "bm25_zero_score_filter": True,
            "tie_break": (
                "dense_rank_then_sparse_rank_then_block_id"
            ),
        },
        "corpus": {
            "chunks": len(
                chunks
            ),
            "answerable_queries": len(
                answerable_cases
            ),
        },
        "runtime": {
            "model_load_seconds": (
                load_time
            ),
            "corpus_encode_seconds": (
                corpus_time
            ),
            "query_encode_seconds": (
                query_time
            ),
            "peak_cuda_memory_gb": (
                peak_vram
            ),
        },
        "aggregate_metrics": {
            "bm25": (
                bm25_aggregate
            ),
            "dense": (
                dense_aggregate
            ),
            "weighted_hybrid": (
                hybrid_aggregate
            ),
        },
        "per_query": (
            per_query_results
        ),
    }

    with results_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"Results saved           : "
        f"{results_path}"
    )


if __name__ == "__main__":
    main()