from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CALIBRATION_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "evidence_sufficiency_calibration_v1.json"
)

CHUNKS_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
)

AUDIT_DIR = (
    PROJECT_ROOT
    / "evaluation"
    / "audits"
)

JSON_OUTPUT = (
    AUDIT_DIR
    / "evidence_sufficiency_negative_label_audit_candidates_v1.json"
)

MARKDOWN_OUTPUT = (
    AUDIT_DIR
    / "evidence_sufficiency_negative_label_audit_candidates_v1.md"
)

EXPECTED_CALIBRATION_SHA256 = (
    "4ece4e35de1f46888f75f4dcae624e34b8e8f2696959f162a5f434615b021ad5"
)

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

QUERY_INSTRUCTION = (
    "Instruct: Given a medical education query, retrieve the passages "
    "from the available medical sources that most directly support the "
    "requested claim. Respect any source explicitly requested by the "
    "query. Do not assume every query targets a guideline.\nQuery:"
)

SOURCE_LABELS = {
    "DOC-WHO-CARD-0001": (
        "World Health Organization (WHO) primary guideline: "
        "Guideline for the pharmacological treatment of "
        "hypertension in adults"
    ),
    "DOC-PMC-CARD-0002": (
        "PMC scientific review article: "
        "Outpatient management of essential hypertension: "
        "a review based on the latest clinical guidelines"
    ),
}

TOP_BLOCKS_PER_PROBE = 10
TOP_LEXICAL_BLOCKS = 10
TOP_REQUIRED_SOURCE_BLOCKS = 8

TOKEN_RE = re.compile(
    r"[A-Za-z0-9]+|[\u0600-\u06FF]+",
    flags=re.UNICODE,
)

EN_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "does", "for",
    "from", "how", "in", "is", "it", "of", "on", "or", "the", "this",
    "to", "what", "when", "which", "with", "would", "should", "could",
    "according", "review", "guideline", "patient", "patients",
}

AR_STOPWORDS = {
    "إيه", "ايه", "ما", "ماذا", "هل", "في", "من", "على", "عن", "إلى",
    "الى", "و", "أو", "او", "ده", "دي", "اللي", "حسب", "كام", "قد",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def block_key(
    document_id: str,
    block_index: int,
) -> str:
    return (
        f"{document_id}:B"
        f"{int(block_index):04d}"
    )


def chunk_block_key(
    chunk: dict[str, Any],
) -> str:
    return block_key(
        str(chunk["document_id"]),
        int(chunk["source_block_index"]),
    )


def build_retrieval_text(
    chunk: dict[str, Any],
) -> str:
    section_path = chunk.get(
        "retrieval_section_path"
    )

    if (
        not isinstance(section_path, list)
        or not section_path
    ):
        section_path = chunk.get(
            "section_path",
            [],
        )

    if isinstance(section_path, list):
        section_text = " > ".join(
            str(item)
            for item in section_path
        )
    else:
        section_text = str(
            section_path
        )

    topics = chunk.get(
        "topics",
        [],
    )

    if isinstance(topics, list):
        topic_text = ", ".join(
            str(item)
            for item in topics
        )
    else:
        topic_text = str(
            topics
        )

    document_id = str(
        chunk.get(
            "document_id",
            "",
        )
    )

    source_label = SOURCE_LABELS.get(
        document_id,
        document_id,
    )

    parts = [
        f"Source document: {source_label}",
        (
            "Medical specialty: "
            f"{chunk.get('medical_specialty', '')}"
        ),
        f"Topics: {topic_text}",
        f"Section: {section_text}",
        (
            "Heading: "
            f"{chunk.get('heading', '')}"
        ),
        (
            "Evidence type: "
            f"{chunk.get('block_type', '')}"
        ),
        (
            "Content: "
            f"{chunk.get('text', '')}"
        ),
    ]

    return "\n".join(
        part
        for part in parts
        if part.strip()
    )


def normalize_tokens(
    text: str,
) -> list[str]:
    tokens = []

    for raw in TOKEN_RE.findall(
        text.casefold()
    ):
        token = raw.strip()

        if not token:
            continue

        if token in EN_STOPWORDS:
            continue

        if token in AR_STOPWORDS:
            continue

        if len(token) == 1:
            continue

        tokens.append(token)

    return tokens


def lexical_rank(
    query_text: str,
    block_texts: dict[str, str],
) -> list[tuple[str, float, list[str]]]:
    query_tokens = set(
        normalize_tokens(query_text)
    )

    if not query_tokens:
        return []

    doc_freq = Counter()

    token_sets: dict[
        str,
        set[str],
    ] = {}

    for key, text in block_texts.items():
        token_set = set(
            normalize_tokens(text)
        )
        token_sets[key] = token_set

        for token in query_tokens:
            if token in token_set:
                doc_freq[token] += 1

    total_docs = max(
        1,
        len(block_texts),
    )

    rows = []

    for key, token_set in token_sets.items():
        matched = sorted(
            query_tokens
            & token_set
        )

        if not matched:
            continue

        score = 0.0

        for token in matched:
            df = doc_freq[token]
            idf = math.log(
                (total_docs + 1)
                / (df + 1)
            ) + 1.0
            score += idf

        score /= math.sqrt(
            max(1, len(query_tokens))
        )

        rows.append(
            (
                key,
                float(score),
                matched,
            )
        )

    rows.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return rows


def git_head() -> str | None:
    git_exe = (
        r"C:\Program Files\Git\cmd\git.exe"
    )

    try:
        proc = subprocess.run(
            [
                git_exe,
                "rev-parse",
                "HEAD",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
    except OSError:
        return None

    if proc.returncode != 0:
        return None

    value = proc.stdout.strip()

    return value or None


def full_block_text(
    chunks: list[dict[str, Any]],
) -> str:
    parts: list[str] = []

    for chunk in chunks:
        text = str(
            chunk.get(
                "text",
                "",
            )
        ).strip()

        if (
            text
            and (
                not parts
                or text != parts[-1]
            )
        ):
            parts.append(text)

    return "\n\n".join(parts)


def block_metadata(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    first = chunks[0]

    section_path = first.get(
        "retrieval_section_path"
    )

    if (
        not isinstance(section_path, list)
        or not section_path
    ):
        section_path = first.get(
            "section_path",
            [],
        )

    return {
        "document_id": str(
            first.get(
                "document_id",
                "",
            )
        ),
        "block_index": int(
            first["source_block_index"]
        ),
        "block_type": first.get(
            "block_type"
        ),
        "heading": first.get(
            "heading"
        ),
        "section_path": section_path,
    }


def semantic_rank_unique_blocks(
    query_embedding: np.ndarray,
    document_embeddings: np.ndarray,
    chunks: list[dict[str, Any]],
) -> list[tuple[str, float]]:
    scores = (
        document_embeddings
        @ query_embedding
    )

    best_score_by_block: dict[
        str,
        float,
    ] = defaultdict(
        lambda: float("-inf")
    )

    for chunk, score in zip(
        chunks,
        scores,
    ):
        key = chunk_block_key(
            chunk
        )
        value = float(score)

        if (
            value
            > best_score_by_block[key]
        ):
            best_score_by_block[
                key
            ] = value

    return sorted(
        best_score_by_block.items(),
        key=lambda item: item[1],
        reverse=True,
    )


def probe_definitions(
    case: dict[str, Any],
) -> list[tuple[str, str]]:
    probes = [
        (
            "query",
            str(case["query"]),
        ),
        (
            "target_concept",
            str(
                case["target_concept"]
            ),
        ),
    ]

    missing_support = case.get(
        "missing_support"
    )

    if (
        isinstance(
            missing_support,
            str,
        )
        and missing_support.strip()
    ):
        probes.append(
            (
                "missing_support",
                missing_support.strip(),
            )
        )

    return probes


def markdown_escape(
    value: Any,
) -> str:
    text = str(value)

    return (
        text
        .replace("|", r"\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def main() -> None:
    print(
        "\nMedicalPlab Full-Corpus "
        "Negative-Label Audit Candidate Generator"
    )
    print("=" * 76)

    if not CALIBRATION_PATH.exists():
        raise FileNotFoundError(
            f"Calibration file not found: "
            f"{CALIBRATION_PATH}"
        )

    actual_calibration_sha = (
        sha256_file(
            CALIBRATION_PATH
        )
    )

    if (
        actual_calibration_sha
        != EXPECTED_CALIBRATION_SHA256
    ):
        raise RuntimeError(
            "Calibration draft SHA-256 mismatch.\n"
            f"Expected: "
            f"{EXPECTED_CALIBRATION_SHA256}\n"
            f"Actual:   "
            f"{actual_calibration_sha}\n"
            "Do not audit a mutated calibration set "
            "without reviewing the changes first."
        )

    calibration = load_json(
        CALIBRATION_PATH
    )

    all_cases = calibration.get(
        "cases",
        [],
    )

    if not isinstance(
        all_cases,
        list,
    ):
        raise ValueError(
            "Calibration cases must be a list."
        )

    audit_cases = [
        case
        for case in all_cases
        if case.get(
            "support_label"
        )
        in {
            "partial",
            "unsupported",
        }
    ]

    if len(audit_cases) != 28:
        raise RuntimeError(
            "Expected 28 partial/unsupported "
            f"cases, found {len(audit_cases)}."
        )

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is required for this audit "
            "to match the selected retrieval baseline."
        )

    chunks: list[
        dict[str, Any]
    ] = []

    chunk_file_hashes: dict[
        str,
        str,
    ] = {}

    block_chunks: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    document_ids = calibration.get(
        "corpus_document_ids",
        [],
    )

    for document_id in document_ids:
        path = (
            CHUNKS_DIR
            / f"{document_id}.chunks.json"
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Chunk file not found: {path}"
            )

        chunk_file_hashes[
            str(document_id)
        ] = sha256_file(path)

        document = load_json(path)

        document_chunks = document.get(
            "chunks",
            [],
        )

        if not isinstance(
            document_chunks,
            list,
        ):
            raise ValueError(
                f"chunks is not a list: {path}"
            )

        for chunk in document_chunks:
            if not isinstance(
                chunk,
                dict,
            ):
                raise ValueError(
                    f"Invalid chunk in {path}"
                )

            actual_document_id = str(
                chunk.get(
                    "document_id",
                    "",
                )
            )

            if (
                actual_document_id
                != document_id
            ):
                raise ValueError(
                    "Chunk document mismatch: "
                    f"expected={document_id}, "
                    f"found={actual_document_id}"
                )

            chunks.append(chunk)

            block_chunks[
                chunk_block_key(
                    chunk
                )
            ].append(chunk)

    if len(chunks) != 227:
        raise RuntimeError(
            "Expected 227 chunks in the current "
            f"two-document corpus, found {len(chunks)}."
        )

    if len(block_chunks) != 192:
        raise RuntimeError(
            "Expected 192 unique source blocks, "
            f"found {len(block_chunks)}."
        )

    block_texts = {
        key: full_block_text(
            value
        )
        for key, value in block_chunks.items()
    }

    corpus_index = []

    for key in sorted(
        block_chunks
    ):
        meta = block_metadata(
            block_chunks[key]
        )

        corpus_index.append(
            {
                "block_key": key,
                **meta,
                "text": block_texts[key],
            }
        )

    print(
        f"Calibration SHA   : "
        f"{actual_calibration_sha}"
    )
    print(
        f"Audit cases       : "
        f"{len(audit_cases)}"
    )
    print(
        f"Corpus chunks     : "
        f"{len(chunks)}"
    )
    print(
        f"Unique blocks     : "
        f"{len(block_chunks)}"
    )
    print(
        f"GPU               : "
        f"{torch.cuda.get_device_name(0)}"
    )
    print(
        f"Model             : "
        f"{MODEL_NAME}"
    )
    print(
        "Retrieval mode    : "
        "source-aware dense retrieval"
    )

    documents = [
        build_retrieval_text(
            chunk
        )
        for chunk in chunks
    ]

    print(
        "\nLoading embedding model..."
    )

    load_start = time.perf_counter()

    model = SentenceTransformer(
        MODEL_NAME,
        device="cuda",
        model_kwargs={
            "torch_dtype": (
                torch.float16
            ),
        },
        tokenizer_kwargs={
            "padding_side": "left",
        },
    )

    model.max_seq_length = 2048

    print(
        "Model loaded      : "
        f"{time.perf_counter() - load_start:.2f}s"
    )

    print(
        "\nEncoding full corpus..."
    )

    document_embeddings = model.encode(
        documents,
        batch_size=4,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    probe_rows: list[
        tuple[str, str, str]
    ] = []

    for case in audit_cases:
        for probe_name, probe_text in (
            probe_definitions(case)
        ):
            probe_rows.append(
                (
                    str(case["case_id"]),
                    probe_name,
                    probe_text,
                )
            )

    probe_texts = [
        row[2]
        for row in probe_rows
    ]

    print(
        "\nEncoding audit probes..."
    )

    probe_embeddings = model.encode(
        probe_texts,
        prompt=QUERY_INSTRUCTION,
        batch_size=4,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embeddings_by_probe: dict[
        tuple[str, str],
        np.ndarray,
    ] = {}

    for row, embedding in zip(
        probe_rows,
        probe_embeddings,
    ):
        case_id, probe_name, _ = row
        embeddings_by_probe[
            (
                case_id,
                probe_name,
            )
        ] = embedding

    audit_case_rows = []

    for index, case in enumerate(
        audit_cases,
        start=1,
    ):
        case_id = str(
            case["case_id"]
        )

        print(
            f"Auditing {index:02d}/"
            f"{len(audit_cases)}: "
            f"{case_id}"
        )

        semantic_probes = []
        candidate_keys: set[
            str
        ] = set()

        original_query_ranking: list[
            tuple[str, float]
        ] = []

        for probe_name, probe_text in (
            probe_definitions(case)
        ):
            embedding = (
                embeddings_by_probe[
                    (
                        case_id,
                        probe_name,
                    )
                ]
            )

            ranking = (
                semantic_rank_unique_blocks(
                    embedding,
                    document_embeddings,
                    chunks,
                )
            )

            top_rows = ranking[
                :TOP_BLOCKS_PER_PROBE
            ]

            if probe_name == "query":
                original_query_ranking = (
                    ranking
                )

            semantic_probes.append(
                {
                    "probe_name": (
                        probe_name
                    ),
                    "probe_text": (
                        probe_text
                    ),
                    "top_blocks": [
                        {
                            "block_key": key,
                            "score": score,
                            "document_id": (
                                block_metadata(
                                    block_chunks[
                                        key
                                    ]
                                )[
                                    "document_id"
                                ]
                            ),
                            "heading": (
                                block_metadata(
                                    block_chunks[
                                        key
                                    ]
                                )[
                                    "heading"
                                ]
                            ),
                        }
                        for key, score
                        in top_rows
                    ],
                }
            )

            candidate_keys.update(
                key
                for key, _
                in top_rows
            )

        combined_lexical_text = " ".join(
            text
            for _, text
            in probe_definitions(case)
        )

        lexical_rows = lexical_rank(
            combined_lexical_text,
            block_texts,
        )[
            :TOP_LEXICAL_BLOCKS
        ]

        candidate_keys.update(
            key
            for key, _, _
            in lexical_rows
        )

        required_document_id = case.get(
            "required_document_id"
        )

        required_source_rows = []

        if (
            isinstance(
                required_document_id,
                str,
            )
            and required_document_id
        ):
            required_source_rows = [
                (
                    key,
                    score,
                )
                for key, score
                in original_query_ranking
                if key.startswith(
                    f"{required_document_id}:B"
                )
            ][
                :TOP_REQUIRED_SOURCE_BLOCKS
            ]

            candidate_keys.update(
                key
                for key, _
                in required_source_rows
            )

        supporting_keys = []

        for block in case.get(
            "supporting_blocks",
            [],
        ):
            key = block_key(
                str(
                    block[
                        "document_id"
                    ]
                ),
                int(
                    block[
                        "block_index"
                    ]
                ),
            )
            supporting_keys.append(
                key
            )
            candidate_keys.add(key)

        per_probe_scores: dict[
            str,
            dict[str, float],
        ] = defaultdict(dict)

        for probe in semantic_probes:
            probe_name = str(
                probe[
                    "probe_name"
                ]
            )

            for row in probe[
                "top_blocks"
            ]:
                per_probe_scores[
                    str(
                        row[
                            "block_key"
                        ]
                    )
                ][probe_name] = float(
                    row[
                        "score"
                    ]
                )

        candidate_rows = []

        lexical_by_key = {
            key: {
                "score": score,
                "matched_tokens": (
                    matched
                ),
            }
            for key, score, matched
            in lexical_rows
        }

        required_by_key = {
            key: score
            for key, score
            in required_source_rows
        }

        for key in candidate_keys:
            meta = block_metadata(
                block_chunks[key]
            )

            semantic_scores = (
                per_probe_scores.get(
                    key,
                    {},
                )
            )

            max_semantic = max(
                semantic_scores.values(),
                default=float("-inf"),
            )

            candidate_rows.append(
                {
                    "block_key": key,
                    **meta,
                    "semantic_scores": (
                        semantic_scores
                    ),
                    "max_semantic_score": (
                        None
                        if max_semantic
                        == float("-inf")
                        else float(
                            max_semantic
                        )
                    ),
                    "lexical": (
                        lexical_by_key.get(
                            key
                        )
                    ),
                    "required_source_query_score": (
                        required_by_key.get(
                            key
                        )
                    ),
                    "is_labeled_support": (
                        key
                        in supporting_keys
                    ),
                    "text": (
                        block_texts[key]
                    ),
                }
            )

        candidate_rows.sort(
            key=lambda row: (
                row[
                    "max_semantic_score"
                ]
                if isinstance(
                    row[
                        "max_semantic_score"
                    ],
                    float,
                )
                else -999.0
            ),
            reverse=True,
        )

        audit_case_rows.append(
            {
                "case_id": case_id,
                "support_label": (
                    case.get(
                        "support_label"
                    )
                ),
                "negative_type": (
                    case.get(
                        "negative_type"
                    )
                ),
                "expected_action": (
                    case.get(
                        "expected_action"
                    )
                ),
                "language": (
                    case.get(
                        "language"
                    )
                ),
                "claim_type": (
                    case.get(
                        "claim_type"
                    )
                ),
                "query": (
                    case.get(
                        "query"
                    )
                ),
                "target_concept": (
                    case.get(
                        "target_concept"
                    )
                ),
                "missing_support": (
                    case.get(
                        "missing_support"
                    )
                ),
                "required_document_id": (
                    required_document_id
                ),
                "contrast_group_id": (
                    case.get(
                        "contrast_group_id"
                    )
                ),
                "supporting_block_keys": (
                    supporting_keys
                ),
                "semantic_probes": (
                    semantic_probes
                ),
                "lexical_top_blocks": [
                    {
                        "block_key": key,
                        "score": score,
                        "matched_tokens": (
                            matched
                        ),
                    }
                    for key, score, matched
                    in lexical_rows
                ],
                "required_source_top_blocks": [
                    {
                        "block_key": key,
                        "score": score,
                    }
                    for key, score
                    in required_source_rows
                ],
                "candidate_blocks": (
                    candidate_rows
                ),
                "manual_review": {
                    "status": (
                        "pending"
                    ),
                    "verdict": None,
                    "reviewer_rationale": (
                        None
                    ),
                },
            }
        )

    AUDIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "audit_id": (
            "medicalplab-evidence-"
            "sufficiency-negative-label-"
            "audit-candidates-v1"
        ),
        "version": "1.0.0",
        "generated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "purpose": (
            "Full-corpus candidate surfacing "
            "for manual verification of all "
            "partial and unsupported labels. "
            "Semantic ranking is diagnostic "
            "only and is not used as gold."
        ),
        "status": (
            "candidate_generation_only_"
            "manual_review_required"
        ),
        "calibration_file": (
            "evaluation/"
            "evidence_sufficiency_"
            "calibration_v1.json"
        ),
        "calibration_sha256": (
            actual_calibration_sha
        ),
        "git_head": git_head(),
        "corpus": {
            "document_ids": (
                document_ids
            ),
            "chunk_count": (
                len(chunks)
            ),
            "unique_block_count": (
                len(block_chunks)
            ),
            "chunk_file_sha256": (
                chunk_file_hashes
            ),
        },
        "candidate_generation": {
            "model": MODEL_NAME,
            "device": "cuda",
            "dtype": "float16",
            "max_seq_length": 2048,
            "normalize_embeddings": True,
            "retrieval_representation": (
                "source-aware"
            ),
            "query_instruction": (
                QUERY_INSTRUCTION
            ),
            "top_blocks_per_probe": (
                TOP_BLOCKS_PER_PROBE
            ),
            "top_lexical_blocks": (
                TOP_LEXICAL_BLOCKS
            ),
            "top_required_source_blocks": (
                TOP_REQUIRED_SOURCE_BLOCKS
            ),
            "warning": (
                "Candidate ranking does not "
                "prove absence of evidence. "
                "Manual review must use the "
                "complete corpus index included "
                "in this artifact."
            ),
        },
        "summary": {
            "audit_case_count": (
                len(audit_case_rows)
            ),
            "partial_count": sum(
                1
                for row in audit_case_rows
                if row[
                    "support_label"
                ]
                == "partial"
            ),
            "unsupported_count": sum(
                1
                for row in audit_case_rows
                if row[
                    "support_label"
                ]
                == "unsupported"
            ),
            "manual_reviews_pending": (
                len(audit_case_rows)
            ),
        },
        "cases": audit_case_rows,
        "corpus_index": corpus_index,
    }

    JSON_OUTPUT.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    md: list[str] = []

    md.append(
        "# MedicalPlab Evidence Sufficiency "
        "Negative-Label Audit Candidates v1"
    )
    md.append("")
    md.append(
        "> Candidate-generation artifact only. "
        "Manual review is required before any "
        "partial or unsupported label is treated "
        "as audited."
    )
    md.append("")
    md.append("## Provenance")
    md.append("")
    md.append(
        f"- Calibration SHA-256: "
        f"`{actual_calibration_sha}`"
    )
    md.append(
        f"- Git HEAD: "
        f"`{artifact['git_head']}`"
    )
    md.append(
        f"- Model: `{MODEL_NAME}`"
    )
    md.append(
        "- Retrieval representation: "
        "`source-aware`"
    )
    md.append(
        f"- Corpus: `{len(chunks)}` chunks / "
        f"`{len(block_chunks)}` unique blocks"
    )
    md.append(
        f"- Audit cases: "
        f"`{len(audit_case_rows)}` "
        "(12 partial + 16 unsupported)"
    )
    md.append("")
    md.append(
        "Semantic rankings below are used only "
        "to surface likely evidence. They do not "
        "define the gold label. The complete "
        "192-block corpus index is included at "
        "the end for manual search and review."
    )
    md.append("")
    md.append("## Case review packets")
    md.append("")

    for row in audit_case_rows:
        md.append(
            f"### {row['case_id']} — "
            f"{row['support_label']} / "
            f"{row['negative_type']}"
        )
        md.append("")
        md.append(
            f"**Query:** "
            f"{row['query']}"
        )
        md.append("")
        md.append(
            f"**Target concept:** "
            f"{row['target_concept']}"
        )
        md.append("")
        md.append(
            f"**Missing support:** "
            f"{row['missing_support']}"
        )
        md.append("")
        md.append(
            f"**Required document:** "
            f"`{row['required_document_id']}`"
        )
        md.append("")
        md.append(
            "**Labeled supporting blocks:** "
            + (
                ", ".join(
                    f"`{key}`"
                    for key
                    in row[
                        "supporting_block_keys"
                    ]
                )
                if row[
                    "supporting_block_keys"
                ]
                else "none"
            )
        )
        md.append("")
        md.append(
            "**Manual review:** "
            "`PENDING`"
        )
        md.append("")

        for probe in row[
            "semantic_probes"
        ]:
            md.append(
                f"#### Semantic probe: "
                f"{probe['probe_name']}"
            )
            md.append("")
            md.append(
                f"`{probe['probe_text']}`"
            )
            md.append("")
            md.append(
                "| Rank | Block | Score | "
                "Document | Heading |"
            )
            md.append(
                "| ---: | --- | ---: | --- | --- |"
            )

            for rank, block in enumerate(
                probe["top_blocks"],
                start=1,
            ):
                md.append(
                    "| "
                    f"{rank} | "
                    f"`{block['block_key']}` | "
                    f"{block['score']:.6f} | "
                    f"{markdown_escape(block['document_id'])} | "
                    f"{markdown_escape(block['heading'])} |"
                )

            md.append("")

        md.append(
            "#### Lexical candidate blocks"
        )
        md.append("")
        md.append(
            "| Rank | Block | Score | Matched terms |"
        )
        md.append(
            "| ---: | --- | ---: | --- |"
        )

        for rank, block in enumerate(
            row[
                "lexical_top_blocks"
            ],
            start=1,
        ):
            matched = ", ".join(
                block[
                    "matched_tokens"
                ]
            )

            md.append(
                "| "
                f"{rank} | "
                f"`{block['block_key']}` | "
                f"{block['score']:.6f} | "
                f"{markdown_escape(matched)} |"
            )

        md.append("")
        md.append(
            "#### Candidate block texts"
        )
        md.append("")

        for block in row[
            "candidate_blocks"
        ]:
            md.append(
                f"##### {block['block_key']}"
            )
            md.append("")
            md.append(
                f"- Document: "
                f"`{block['document_id']}`"
            )
            md.append(
                f"- Type: "
                f"`{block['block_type']}`"
            )
            md.append(
                f"- Heading: "
                f"{block['heading']}"
            )
            md.append(
                f"- Labeled support: "
                f"`{block['is_labeled_support']}`"
            )
            md.append("")
            md.append(
                block["text"]
            )
            md.append("")

        md.append("---")
        md.append("")

    md.append(
        "## Complete full-corpus block index"
    )
    md.append("")
    md.append(
        "This appendix contains every unique "
        "source block in the current two-document "
        "corpus. It is included so manual label "
        "review is not limited to retriever-ranked "
        "candidates."
    )
    md.append("")

    for block in corpus_index:
        md.append(
            f"### {block['block_key']}"
        )
        md.append("")
        md.append(
            f"- Document: "
            f"`{block['document_id']}`"
        )
        md.append(
            f"- Type: "
            f"`{block['block_type']}`"
        )
        md.append(
            f"- Heading: "
            f"{block['heading']}"
        )
        md.append("")
        md.append(
            block["text"]
        )
        md.append("")

    MARKDOWN_OUTPUT.write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    json_sha = sha256_file(
        JSON_OUTPUT
    )
    md_sha = sha256_file(
        MARKDOWN_OUTPUT
    )

    print()
    print(
        "Full-corpus candidate generation: PASS"
    )
    print(
        f"JSON     : "
        f"{JSON_OUTPUT.relative_to(PROJECT_ROOT)}"
    )
    print(
        f"JSON SHA : {json_sha}"
    )
    print(
        f"Markdown : "
        f"{MARKDOWN_OUTPUT.relative_to(PROJECT_ROOT)}"
    )
    print(
        f"MD SHA   : {md_sha}"
    )
    print(
        "Labels changed     : 0"
    )
    print(
        "Manual reviews     : "
        f"{len(audit_case_rows)} pending"
    )
    print()
    print(
        "Next: manually adjudicate all 28 "
        "partial/unsupported labels using the "
        "candidate packets and complete corpus "
        "appendix."
    )


if __name__ == "__main__":
    main()
