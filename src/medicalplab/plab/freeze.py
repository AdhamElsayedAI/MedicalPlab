"""Golden dataset freeze specification and packaging for MedicalPlab."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .pilot import PLABPilotService


GOLDEN_DATASET_ID = "medicalplab-cardiorespiratory-golden-v1"
SOURCE_BATCH_ID = "cardiorespiratory_batch_1_v1"
CORPUS_SNAPSHOT_ID = "corpus_cardiorespiratory_snapshot_v1"


@dataclass(frozen=True)
class GoldenDatasetFreeze:
    golden_dataset_id: str
    source_batch_id: str
    corpus_snapshot_id: str
    created_at: str
    golden_count: int
    total_batch_questions: int
    question_ids: tuple[str, ...]
    question_versions: dict[str, int]
    question_content_sha256: dict[str, str]
    reviewer_ids: dict[str, str]
    review_timestamps: dict[str, str]
    code_commit_sha: str | None
    freeze_sha256: str
    golden_questions: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_golden_dataset_freeze(
    service: "PLABPilotService",
    commit_sha: str | None = None,
) -> GoldenDatasetFreeze:
    """Create an immutable Golden Dataset Freeze package.

    Fails closed if 0 questions are golden.
    """
    golden_qids = [qid for qid in service.questions if service.is_golden(qid)]
    if not golden_qids:
        raise ValueError(
            "CANNOT_FREEZE_EMPTY_DATASET: 0 questions have satisfied the Golden promotion gate. "
            "Real clinician review and approval is required before freezing Golden v1."
        )

    versions = {}
    hashes = {}
    reviewers = {}
    timestamps = {}
    frozen_items = []

    for qid in golden_qids:
        q = service.questions[qid]
        review = service.reviews[qid]
        versions[qid] = review.question_version
        hashes[qid] = review.question_content_sha256
        reviewers[qid] = review.reviewer_id or "UNKNOWN"
        timestamps[qid] = review.reviewed_at or "UNKNOWN"
        frozen_items.append(
            {
                **dict(q),
                "question_version": review.question_version,
                "question_content_sha256": review.question_content_sha256,
                "reviewer_id": review.reviewer_id,
                "reviewed_at": review.reviewed_at,
                "final_decision": "APPROVED",
                "golden_status": True,
            }
        )

    payload_for_hashing = {
        "golden_dataset_id": GOLDEN_DATASET_ID,
        "source_batch_id": SOURCE_BATCH_ID,
        "corpus_snapshot_id": CORPUS_SNAPSHOT_ID,
        "golden_count": len(golden_qids),
        "question_ids": sorted(golden_qids),
        "versions": versions,
        "hashes": hashes,
    }
    freeze_sha = hashlib.sha256(
        json.dumps(payload_for_hashing, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    return GoldenDatasetFreeze(
        golden_dataset_id=GOLDEN_DATASET_ID,
        source_batch_id=SOURCE_BATCH_ID,
        corpus_snapshot_id=CORPUS_SNAPSHOT_ID,
        created_at=datetime.now(timezone.utc).isoformat(),
        golden_count=len(golden_qids),
        total_batch_questions=len(service.questions),
        question_ids=tuple(sorted(golden_qids)),
        question_versions=versions,
        question_content_sha256=hashes,
        reviewer_ids=reviewers,
        review_timestamps=timestamps,
        code_commit_sha=commit_sha,
        freeze_sha256=freeze_sha,
        golden_questions=frozen_items,
    )
