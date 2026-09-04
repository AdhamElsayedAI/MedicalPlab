import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


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


TOP_K_VALUES = (1, 3, 5, 10)


def load_json(path: Path) -> dict[str, Any]:
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


def tokenize(text: str) -> list[str]:
    text = text.lower()

    tokens = re.findall(
        r"[a-z0-9]+|[\u0600-\u06ff]+",
        text,
    )

    return tokens


class BM25:
    def __init__(
        self,
        documents: list[list[str]],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
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
            if self.doc_count
            else 0.0
        )

        self.term_frequencies = [
            Counter(document)
            for document in documents
        ]

        document_frequency: Counter[str] = Counter()

        for document in documents:
            for token in set(document):
                document_frequency[
                    token
                ] += 1

        self.idf: dict[str, float] = {}

        for token, frequency in (
            document_frequency.items()
        ):
            self.idf[token] = math.log(
                1
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
        frequencies = (
            self.term_frequencies[
                document_index
            ]
        )

        document_length = (
            self.doc_lengths[
                document_index
            ]
        )

        score = 0.0

        for token in query_tokens:
            if token not in frequencies:
                continue

            term_frequency = frequencies[
                token
            ]

            idf = self.idf.get(
                token,
                0.0,
            )

            denominator = (
                term_frequency
                + self.k1
                * (
                    1
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
                    + 1
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
                index,
            )
            for index in range(
                self.doc_count
            )
        ]


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
    top_k = ranked_blocks[:k]

    return float(
        any(
            block in relevant_blocks
            for block in top_k
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
    actual = dcg_at_k(
        ranked_blocks,
        relevance_map,
        k,
    )

    ideal_relevances = sorted(
        relevance_map.values(),
        reverse=True,
    )

    ideal_score = 0.0

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

        ideal_score += (
            gain
            / discount
        )

    if ideal_score == 0.0:
        return 0.0

    return (
        actual
        / ideal_score
    )


def build_retrieval_text(
    chunk: dict[str, Any],
) -> str:
    section_path = chunk.get(
        "section_path",
        [],
    )

    if isinstance(
        section_path,
        list,
    ):
        section_text = " > ".join(
            str(item)
            for item in section_path
        )
    else:
        section_text = str(
            section_path
        )

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
        section_text,
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
        if part
    )


def rank_unique_blocks(
    chunks: list[dict[str, Any]],
    scores: list[float],
) -> list[int]:
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

        if (
            score
            > best_score_by_block[
                block_index
            ]
        ):
            best_score_by_block[
                block_index
            ] = score

    ranked = sorted(
        best_score_by_block.items(),
        key=lambda item: (
            item[1]
        ),
        reverse=True,
    )

    return [
        block_index
        for block_index, _
        in ranked
    ]


def main() -> None:
    chunk_document = load_json(
        CHUNKS_PATH
    )

    evaluation = load_json(
        EVAL_PATH
    )

    chunks = chunk_document.get(
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

    retrieval_texts = [
        build_retrieval_text(
            chunk
        )
        for chunk in chunks
    ]

    tokenized_documents = [
        tokenize(text)
        for text in retrieval_texts
    ]

    bm25 = BM25(
        tokenized_documents
    )

    answerable_cases = [
        case
        for case in cases
        if case.get(
            "expected_answerable"
        )
    ]

    aggregate_hits = {
        k: []
        for k in TOP_K_VALUES
    }

    aggregate_recalls = {
        k: []
        for k in TOP_K_VALUES
    }

    reciprocal_ranks: list[float] = []

    ndcg_scores: list[float] = []

    print(
        "\nMedicalPlab BM25 Retrieval Benchmark"
    )
    print("=" * 56)

    print(
        f"Chunks indexed       : "
        f"{len(chunks)}"
    )

    print(
        f"Evaluation cases     : "
        f"{len(cases)}"
    )

    print(
        f"Answerable evaluated : "
        f"{len(answerable_cases)}"
    )

    print(
        "\nPer-query results"
    )
    print("-" * 100)

    for case in answerable_cases:
        query_id = case[
            "query_id"
        ]

        query = case[
            "query"
        ]

        query_tokens = tokenize(
            query
        )

        scores = bm25.get_scores(
            query_tokens
        )

        ranked_blocks = (
            rank_unique_blocks(
                chunks,
                scores,
            )
        )

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

        rr = reciprocal_rank(
            ranked_blocks,
            relevant_blocks,
        )

        reciprocal_ranks.append(
            rr
        )

        ndcg = ndcg_at_k(
            ranked_blocks,
            relevance_map,
            10,
        )

        ndcg_scores.append(
            ndcg
        )

        for k in TOP_K_VALUES:
            aggregate_hits[k].append(
                hit_at_k(
                    ranked_blocks,
                    relevant_blocks,
                    k,
                )
            )

            aggregate_recalls[k].append(
                recall_at_k(
                    ranked_blocks,
                    relevant_blocks,
                    k,
                )
            )

        top5 = ranked_blocks[:5]

        print(
            f"{query_id:<9} | "
            f"RR={rr:.3f} | "
            f"nDCG@10={ndcg:.3f} | "
            f"Top5={top5}"
        )

    print(
        "\nAggregate metrics"
    )
    print("-" * 56)

    for k in TOP_K_VALUES:
        hits = aggregate_hits[
            k
        ]

        recalls = aggregate_recalls[
            k
        ]

        mean_hit = (
            sum(hits)
            / len(hits)
            if hits
            else 0.0
        )

        mean_recall = (
            sum(recalls)
            / len(recalls)
            if recalls
            else 0.0
        )

        print(
            f"Hit@{k:<2}     : "
            f"{mean_hit:.4f}"
        )

        print(
            f"Recall@{k:<2}  : "
            f"{mean_recall:.4f}"
        )

    mean_rr = (
        sum(
            reciprocal_ranks
        )
        / len(
            reciprocal_ranks
        )
        if reciprocal_ranks
        else 0.0
    )

    mean_ndcg = (
        sum(
            ndcg_scores
        )
        / len(
            ndcg_scores
        )
        if ndcg_scores
        else 0.0
    )

    print(
        f"MRR         : "
        f"{mean_rr:.4f}"
    )

    print(
        f"nDCG@10     : "
        f"{mean_ndcg:.4f}"
    )


if __name__ == "__main__":
    main()