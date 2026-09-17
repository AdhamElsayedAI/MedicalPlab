"""Pilot-ready PLAB catalog, evaluation, attempts, progress, and telemetry."""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from medicalplab.stage_g.runtime import get_runtime_mode

from .governance import (
    REVIEW_DIMENSIONS,
    ReviewDecision,
    ReviewFinding,
    ReviewRecord,
    ReviewStatus,
    create_revision,
    evaluate_golden_promotion,
    question_content_hash,
)
from .models import PLABCitation, PLABChoice, PLABQuestion, PLABQuestionStatus
from .persistence import SQLitePilotPersistence
from .data_manifest import ACTIVE_BATCH_PATH, REFERENCE_ONLY_DOCUMENT_IDS, verify_production_data_manifest


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class PLABProductError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _question_model(payload: Mapping[str, object]) -> PLABQuestion:
    return PLABQuestion(
        question_id=str(payload["question_id"]),
        stem=str(payload["stem"]),
        choices=tuple(PLABChoice(id=str(c["id"]), text=str(c["text"])) for c in payload["choices"]),
        correct_answer=str(payload["correct_answer"]),
        explanation=str(payload["explanation"]),
        specialty=str(payload["specialty"]),
        topic=str(payload["topic"]),
        learning_objective=str(payload["learning_objective"]),
        difficulty=str(payload["difficulty"]),
        citations=tuple(
            PLABCitation(ref=str(c["ref"]), document_id=str(c["document_id"]), quote=str(c["quote"]))
            for c in payload["citations"]
        ),
        status=PLABQuestionStatus(str(payload.get("status", "needs_review"))),
        schema_version=str(payload.get("schema_version", "plab-question-v1")),
    )


def _review_record(payload: Mapping[str, object], question: Mapping[str, object]) -> ReviewRecord:
    finding = lambda key: ReviewFinding(str(payload[key])) if payload.get(key) else None
    decision = ReviewDecision(str(payload["final_decision"])) if payload.get("final_decision") else None
    return ReviewRecord(
        question_id=str(payload["question_id"]),
        question_version=int(payload.get("question_version", 1)),
        question_content_sha256=str(payload.get("question_content_sha256") or question_content_hash(question)),
        review_status=ReviewStatus(str(payload.get("review_status", "pending"))),
        clinical_correctness=finding("clinical_correctness"),
        sba_unambiguity=finding("sba_unambiguity"),
        uk_alignment=finding("uk_alignment"),
        evidence_adequacy=finding("evidence_adequacy"),
        distractor_quality=finding("distractor_quality"),
        explanation_quality=finding("explanation_quality"),
        reviewer_id=str(payload["reviewer_id"]) if payload.get("reviewer_id") else None,
        reviewer_name=str(payload["reviewer_name"]) if payload.get("reviewer_name") else None,
        review_started_at=str(payload["review_started_at"]) if payload.get("review_started_at") else None,
        reviewed_at=str(payload["reviewed_at"]) if payload.get("reviewed_at") else None,
        review_comments=str(payload["review_comments"]) if payload.get("review_comments") else None,
        revision_notes=str(payload["revision_notes"]) if payload.get("revision_notes") else None,
        final_decision=decision,
        golden_status=bool(payload.get("golden_status", False)),
    )


class PilotTelemetry:
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.timeout_count = 0
        self.latencies_ms: list[float] = []
        self.questions_served = 0
        self.attempts_submitted = 0
        self.correct_attempts = 0
        self.refusal_count = 0
        self.unsupported_query_count = 0
        self.retrieval_latencies_ms: list[float] = []
        self.evidence_outcomes: Counter[str] = Counter()
        self.topic_distribution: Counter[str] = Counter()

    def record_request(self, started: float, success: bool) -> None:
        self.request_count += 1
        self.success_count += int(success)
        self.error_count += int(not success)
        self.latencies_ms.append((time.perf_counter() - started) * 1000)

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        index = round((len(ordered) - 1) * percentile)
        return round(ordered[index], 3)

    def snapshot(self, governance: Mapping[str, int]) -> dict[str, object]:
        return {
            "system": {
                "request_count": self.request_count,
                "success_rate": self.success_count / self.request_count if self.request_count else None,
                "error_rate": self.error_count / self.request_count if self.request_count else None,
                "timeout_count": self.timeout_count,
                "p50_latency_ms": self._percentile(self.latencies_ms, 0.50),
                "p95_latency_ms": self._percentile(self.latencies_ms, 0.95),
            },
            "rag": {
                "p50_retrieval_latency_ms": self._percentile(self.retrieval_latencies_ms, 0.50),
                "evidence_sufficiency_outcomes": dict(self.evidence_outcomes),
                "refusal_count": self.refusal_count,
                "unsupported_query_count": self.unsupported_query_count,
            },
            "plab": {
                "questions_served": self.questions_served,
                "attempts_submitted": self.attempts_submitted,
                "answer_accuracy": self.correct_attempts / self.attempts_submitted if self.attempts_submitted else None,
                "topic_distribution": dict(self.topic_distribution),
            },
            "content_governance": dict(governance),
        }


class PLABPilotService:
    def __init__(
        self,
        questions: list[dict[str, object]],
        reviews: list[dict[str, object]],
        chunk_index: Mapping[str, Mapping[str, str]],
        batch_version: str,
        preview_qa: bool = False,
        persistence: SQLitePilotPersistence | None = None,
    ):
        self.questions = {str(q["question_id"]): dict(q) for q in questions}
        review_payloads = {str(r["question_id"]): r for r in reviews}
        self.review_metadata = {
            qid: {
                "risk_level": payload.get("risk_level"),
                "automated_schema_valid": payload.get("automated_schema_valid"),
                "automated_evidence_valid": payload.get("automated_evidence_valid"),
                "automated_uk_check": payload.get("automated_uk_check"),
            }
            for qid, payload in review_payloads.items()
        }
        self.reviews = {
            qid: _review_record(review_payloads[qid], question)
            for qid, question in self.questions.items()
            if qid in review_payloads
        }
        self.chunk_index = dict(chunk_index)
        self.batch_version = batch_version
        self.preview_qa = preview_qa
        self.persistence = persistence
        self.revisions: dict[str, list[dict[str, object]]] = defaultdict(list)
        self.attempts: dict[tuple[str, str], dict[str, object]] = {}
        self.telemetry = PilotTelemetry()

    @classmethod
    def load_default(
        cls,
        preview_qa: bool = False,
        persistence_path: Path | str | None = None,
        enable_persistence: bool = True,
        data_root: Path | str | None = None,
    ) -> "PLABPilotService":
        if data_root is None:
            data_root = Path(os.environ.get("MEDICALPLAB_DATA_ROOT", str(PROJECT_ROOT / "Data")))
        else:
            data_root = Path(data_root)
        batch_path = data_root / ACTIVE_BATCH_PATH
        queue_path = data_root / "questions" / "cardiorespiratory_batch_1_review_queue.json"
        snapshot_path = data_root / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"
        integrity = verify_production_data_manifest(data_root)
        if not integrity.is_valid:
            raise PLABProductError("PLAB_CONTENT_UNAVAILABLE", "PLAB data integrity validation failed: " + ",".join(integrity.blockers), 503)
        try:
            batch = json.loads(batch_path.read_text(encoding="utf-8"))
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            chunks: dict[str, dict[str, str]] = {}
            for document in snapshot["documents"]:
                if str(document.get("document_id")) in REFERENCE_ONLY_DOCUMENT_IDS:
                    continue
                relative = Path(str(document["chunks_file"]))
                path = data_root / Path(*relative.parts[1:]) if relative.parts and relative.parts[0].lower() == "data" else data_root / relative
                chunk_data = json.loads(path.read_text(encoding="utf-8"))
                for chunk in chunk_data["chunks"]:
                    chunks[str(chunk["chunk_id"])] = {
                        "document_id": str(document["document_id"]),
                        "text": str(chunk["text"]),
                    }
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PLABProductError(
                "PLAB_CONTENT_UNAVAILABLE",
                f"The verified PLAB corpus is unavailable or invalid: {exc}",
                503,
            ) from exc

        persistence = None
        if enable_persistence:
            db_file = Path(persistence_path) if persistence_path else data_root / "persistence" / "pilot_store.db"
            try:
                persistence = SQLitePilotPersistence(db_file)
            except (OSError, sqlite3.Error) as exc:
                raise PLABProductError("PLAB_STORAGE_UNAVAILABLE", "PLAB storage could not be initialized.", 503) from exc

        instance = cls(batch["questions"], queue["queue"], chunks, str(batch["batch_version"]), preview_qa, persistence=persistence)

        if persistence:
            try:
                persisted_reviews = persistence.load_reviews()
                for qid, record in persisted_reviews.items():
                    if qid in instance.reviews:
                        instance.reviews[qid] = record

                persisted_revs, revised_questions = persistence.load_revisions()
                for qid, revs in persisted_revs.items():
                    instance.revisions[qid].extend(revs)
                for qid, q_data in revised_questions.items():
                    instance.questions[qid] = q_data

                persisted_attempts = persistence.load_attempts()
                instance.attempts.update(persisted_attempts)
            except (OSError, sqlite3.Error, ValueError, KeyError, TypeError) as exc:
                raise PLABProductError("PLAB_STORAGE_UNAVAILABLE", "PLAB persisted state could not be loaded.", 503) from exc

        return instance

    def _promotion(self, question_id: str):
        payload = self.questions[question_id]
        review = self.reviews[question_id]
        evidence_texts: list[str] = []
        citation_resolves = True
        for citation in payload["citations"]:
            chunk = self.chunk_index.get(str(citation["ref"]))
            if not chunk or chunk["document_id"] != str(citation["document_id"]):
                citation_resolves = False
                continue
            # Bind each quote to its own cited chunk, not any other citation.
            if " ".join(str(citation["quote"]).casefold().split()) not in " ".join(chunk["text"].casefold().split()):
                citation_resolves = False
            evidence_texts.append(chunk["text"])
        uk_acceptable = review.uk_alignment is ReviewFinding.PASS
        return evaluate_golden_promotion(
            _question_model(payload), payload, review.question_version, review,
            evidence_texts, citation_resolves, uk_acceptable,
        )

    def is_golden(self, question_id: str) -> bool:
        review = self.reviews.get(question_id)
        return bool(review and review.golden_status and self._promotion(question_id).promoted)

    def _is_available(self, question_id: str) -> bool:
        return self.is_golden(question_id) or self.preview_qa

    def list_questions(self) -> list[dict[str, object]]:
        return [self.question_dto(qid) for qid in self.questions if self._is_available(qid)]

    def question_dto(self, question_id: str) -> dict[str, object]:
        if question_id not in self.questions:
            raise PLABProductError("QUESTION_NOT_FOUND", "Question not found.", 404)
        if not self._is_available(question_id):
            raise PLABProductError("QUESTION_NOT_AVAILABLE", "Question is not approved for student use.", 403)
        payload = self.questions[question_id]
        review = self.reviews[question_id]
        self.telemetry.questions_served += 1
        return {
            "question_id": question_id,
            "stem": payload["stem"],
            "options": [{"id": c["id"], "text": c["text"]} for c in payload["choices"]],
            "topic": payload["topic"],
            "specialty": payload.get("specialty", "Cardiorespiratory"),
            "difficulty": payload["difficulty"],
            "question_version": review.question_version,
            "content_mode": "GOLDEN" if self.is_golden(question_id) else "PREVIEW_QA",
            "warning": None if self.is_golden(question_id) else "Not clinically approved; internal QA only.",
        }

    def evaluate(
        self,
        user_id: str,
        question_id: str,
        selected_option: str,
        idempotency_key: str,
        response_time_ms: int | None = None,
    ) -> dict[str, object]:
        started = time.perf_counter()
        try:
            if question_id not in self.questions:
                raise PLABProductError("QUESTION_NOT_FOUND", "Question not found.", 404)
            if not self._is_available(question_id):
                raise PLABProductError("QUESTION_NOT_AVAILABLE", "Question is not approved for student use.", 403)
            if selected_option not in {"A", "B", "C", "D", "E"}:
                raise PLABProductError("INVALID_OPTION", "Selected option must be A, B, C, D, or E.", 422)
            if not idempotency_key.strip():
                raise PLABProductError("IDEMPOTENCY_KEY_REQUIRED", "An idempotency key is required.", 422)
            key = (user_id, idempotency_key.strip())
            existing = self.attempts.get(key)
            if existing:
                if existing["question_id"] != question_id or existing["selected_option"] != selected_option:
                    raise PLABProductError("IDEMPOTENCY_CONFLICT", "Idempotency key was reused for another submission.", 409)
                self.telemetry.record_request(started, True)
                return dict(existing["response"])

            payload = self.questions[question_id]
            review = self.reviews[question_id]
            correct = str(payload["correct_answer"])
            is_correct = selected_option == correct
            attempt_id = f"ATT-{uuid.uuid4().hex.upper()}"
            attempt = {
                "attempt_id": attempt_id,
                "user_id": user_id,
                "idempotency_key": idempotency_key.strip(),
                "question_id": question_id,
                "question_version": review.question_version,
                "batch_version": self.batch_version,
                "topic": payload["topic"],
                "selected_option": selected_option,
                "correct_option": correct,
                "is_correct": is_correct,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "response_time_ms": response_time_ms,
                "runtime_mode": get_runtime_mode().value,
                "question_lifecycle_state": "GOLDEN" if self.is_golden(question_id) else "HUMAN_REVIEW_PENDING_PREVIEW_QA",
            }
            response = {
                "attempt_id": attempt_id,
                "correct": is_correct,
                "selected_answer": selected_option,
                "correct_answer": correct,
                "explanation": payload["explanation"],
                "citations": [
                    {"document_id": c["document_id"], "reference": c["ref"]}
                    for c in payload["citations"]
                ],
                "topic": payload["topic"],
                "learning_feedback": "Review the explanation and cited source." if not is_correct else "Correct. Review the explanation to consolidate the learning point.",
                "question_version": review.question_version,
                "content_mode": "GOLDEN" if self.is_golden(question_id) else "PREVIEW_QA",
            }
            attempt["response"] = response
            if self.persistence:
                try:
                    self.persistence.save_attempt(attempt)
                except sqlite3.IntegrityError as exc:
                    # Another worker may have committed the same retry key.
                    saved = self.persistence.load_attempts().get(key)
                    if saved and saved["question_id"] == question_id and saved["selected_option"] == selected_option:
                        self.attempts[key] = saved
                        return dict(saved["response"])
                    raise PLABProductError("IDEMPOTENCY_CONFLICT", "Submission conflicts with a persisted attempt.", 409) from exc
                except (OSError, sqlite3.Error) as exc:
                    raise PLABProductError("PLAB_STORAGE_UNAVAILABLE", "Attempt was not saved.", 503) from exc
            self.attempts[key] = attempt
            self.telemetry.attempts_submitted += 1
            self.telemetry.correct_attempts += int(is_correct)
            self.telemetry.topic_distribution[str(payload["topic"])] += 1
            self.telemetry.record_request(started, True)
            return dict(response)
        except PLABProductError:
            self.telemetry.record_request(started, False)
            raise

    def progress(self, user_id: str) -> dict[str, object]:
        attempts = [a for (uid, _), a in self.attempts.items() if uid == user_id]
        by_topic: dict[str, list[dict[str, object]]] = defaultdict(list)
        first_attempts: dict[str, int] = {}
        for attempt in attempts:
            qid = str(attempt["question_id"])
            if qid not in first_attempts:
                first_attempts[qid] = int(attempt["is_correct"])
            by_topic[str(attempt["topic"])].append(attempt)
        topic_accuracy = {
            topic: sum(int(a["is_correct"]) for a in values) / len(values)
            for topic, values in by_topic.items()
        }
        ordered = sorted(topic_accuracy.items(), key=lambda item: (item[1], item[0]))
        recent = attempts[-10:]
        total_attempts = len(attempts)
        correct_attempts = sum(int(a["is_correct"]) for a in attempts)
        first_attempt_acc = (
            sum(first_attempts.values()) / len(first_attempts)
            if first_attempts
            else None
        )
        completion = (
            len(first_attempts) / len(self.questions)
            if self.questions
            else 0.0
        )
        return {
            "user_id": user_id,
            "question_count": total_attempts,
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "overall_accuracy": correct_attempts / total_attempts if total_attempts else None,
            "recent_accuracy": sum(int(a["is_correct"]) for a in recent) / len(recent) if recent else None,
            "first_attempt_accuracy": first_attempt_acc,
            "question_completion": round(completion, 4),
            "topic_accuracy": topic_accuracy,
            "weak_topics": [topic for topic, score in ordered if score < 0.6],
            "strongest_topics": [topic for topic, score in reversed(ordered) if score >= 0.8],
            "mastery_model": "descriptive_attempt_metrics",
        }

    def start_review(self, question_id: str, reviewer_id: str, reviewer_name: str | None = None) -> dict[str, object]:
        if question_id not in self.reviews:
            raise PLABProductError("QUESTION_NOT_FOUND", "Question not found.", 404)
        started = self.reviews[question_id].start(reviewer_id, reviewer_name)
        if self.persistence:
            try:
                self.persistence.save_review(started)
            except (OSError, sqlite3.Error) as exc:
                raise PLABProductError("PLAB_STORAGE_UNAVAILABLE", "Review was not saved.", 503) from exc
        self.reviews[question_id] = started
        return self.review_status(question_id)

    def submit_review(
        self,
        question_id: str,
        reviewer_id: str,
        decision: ReviewDecision,
        findings: Mapping[str, ReviewFinding],
        comments: str | None,
        revision_notes: str | None,
    ) -> dict[str, object]:
        record = self.reviews.get(question_id)
        if not record:
            raise PLABProductError("QUESTION_NOT_FOUND", "Question not found.", 404)
        if record.reviewer_id != reviewer_id:
            raise PLABProductError("REVIEWER_MISMATCH", "Only the assigned reviewer may submit this review.", 403)
        try:
            decided = record.decide(decision, findings, comments, revision_notes)
        except ValueError as exc:
            raise PLABProductError(str(exc), "Review decision failed validation.", 422) from exc
        # Clinical approval and publication are distinct actions. An explicit
        # promotion must recheck the current content and evidence before release.
        if self.persistence:
            try:
                self.persistence.save_review(decided)
            except (OSError, sqlite3.Error) as exc:
                raise PLABProductError("PLAB_STORAGE_UNAVAILABLE", "Review decision was not saved.", 503) from exc
        self.reviews[question_id] = decided
        return self.review_status(question_id)

    def revise_question(
        self,
        question_id: str,
        updated: Mapping[str, object],
        revision_reason: str,
        editor_id: str,
    ) -> dict[str, object]:
        if question_id not in self.questions:
            raise PLABProductError("QUESTION_NOT_FOUND", "Question not found.", 404)
        previous = self.questions[question_id]
        merged = {**previous, **dict(updated), "question_id": question_id, "status": "needs_review"}
        review = self.reviews[question_id]
        try:
            revision = create_revision(previous, merged, review.question_version, revision_reason, editor_id, review.revision_notes)
            _question_model(merged)
        except (ValueError, KeyError, TypeError) as exc:
            raise PLABProductError("INVALID_REVISION", str(exc), 422) from exc
        revised_review = ReviewRecord(
            question_id=question_id,
            question_version=revision.version,
            question_content_sha256=revision.content_sha256,
            review_status=ReviewStatus.REVISED,
            revision_notes=revision_reason,
        )
        if self.persistence:
            try:
                self.persistence.save_revision_and_review(revision, merged, revised_review)
            except (OSError, sqlite3.Error) as exc:
                raise PLABProductError("PLAB_STORAGE_UNAVAILABLE", "Question revision was not saved.", 503) from exc
        self.questions[question_id] = merged
        self.revisions[question_id].append(asdict(revision))
        self.reviews[question_id] = revised_review
        return self.review_status(question_id)

    def review_status(self, question_id: str) -> dict[str, object]:
        if question_id not in self.reviews:
            raise PLABProductError("QUESTION_NOT_FOUND", "Question not found.", 404)
        record = asdict(self.reviews[question_id])
        q = self.questions.get(question_id, {})
        return {
            **record,
            "review_status": self.reviews[question_id].review_status.value,
            "final_decision": self.reviews[question_id].final_decision.value if self.reviews[question_id].final_decision else None,
            **{dimension: getattr(self.reviews[question_id], dimension).value if getattr(self.reviews[question_id], dimension) else None for dimension in REVIEW_DIMENSIONS},
            **self.review_metadata.get(question_id, {}),
            "stem": q.get("stem"),
            "choices": q.get("choices"),
            "correct_answer": q.get("correct_answer"),
            "explanation": q.get("explanation"),
            "citations": q.get("citations"),
            "specialty": q.get("specialty"),
            "topic": q.get("topic"),
            "learning_objective": q.get("learning_objective"),
            "revision_history": self.revisions[question_id],
        }

    def check_promotion_eligibility(self, question_id: str) -> dict[str, object]:
        if question_id not in self.questions:
            raise PLABProductError("QUESTION_NOT_FOUND", "Question not found.", 404)
        promotion = self._promotion(question_id)
        review = self.reviews[question_id]
        return {
            "question_id": question_id,
            "eligible": promotion.promoted,
            "error_codes": list(promotion.error_codes),
            "review_status": review.review_status.value,
            "final_decision": review.final_decision.value if review.final_decision else None,
            "golden_status": self.is_golden(question_id),
            "question_version": review.question_version,
            "question_content_sha256": review.question_content_sha256,
        }

    def governance_counts(self) -> dict[str, int]:
        counts = Counter(review.review_status.value for review in self.reviews.values())
        return {
            "golden": sum(self.is_golden(qid) for qid in self.questions),
            "pending": counts["pending"],
            "in_review": counts["in_review"] + counts["re_review"],
            "revised": counts["revise"] + counts["revised"],
            "approved": counts["approved"],
            "rejected": counts["rejected"],
        }
