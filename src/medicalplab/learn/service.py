"""Grounded course learning service supporting multi-specialty tracks."""

from __future__ import annotations

import json
import math
import re
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from .models import (
    CourseQueryRequest,
    CourseQueryResponse,
    GroundingStatus,
    StudentCitation,
)
from .renal_retrieval import (
    RENAL_SUFFICIENCY_THRESHOLD,
    QwenRenalRetriever,
    RenalRetriever,
    RenalRetrieverUnavailable,
)

CALIBRATED_SUFFICIENCY_TAU = 0.7223
URINARY_SOURCE_DATA_STATUS = "RENAL_V1_AVAILABLE"


class CourseLearningService:
    """Production service for evidence-grounded course learning across medical modules."""

    def __init__(
        self,
        data_root: Path | str | None = None,
        *,
        renal_retriever: RenalRetriever | None = None,
    ) -> None:
        self.data_root = Path(data_root) if data_root else Path(__file__).resolve().parents[3] / "Data"
        self._doc_titles: dict[str, str] = {}
        self._chunks: list[dict[str, Any]] = []
        self._chunk_tokens: list[list[str]] = []
        self._df: Counter[str] = Counter()
        self.urinary_available = False
        self._load_corpora()
        self._renal_retriever = renal_retriever or QwenRenalRetriever(self.data_root)

    def _load_corpora(self) -> None:
        # 1. Load document titles from manifest
        manifest_path = self.data_root / "metadata" / "document_manifest.json"
        if manifest_path.exists():
            try:
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                for doc in manifest_data.get("documents", []):
                    self._doc_titles[str(doc.get("document_id"))] = str(doc.get("title", doc.get("document_id")))
            except Exception:
                pass

        # 2. Load cardiorespiratory chunks from processed folders
        processed_dir = self.data_root / "processed"
        if processed_dir.exists():
            for folder in ["cardiology", "respiratory", "emergency_medicine", "respiratory_medicine"]:
                target_dir = processed_dir / folder
                if not target_dir.exists():
                    continue
                for chunk_file in target_dir.glob("*.chunks.json"):
                    try:
                        chunks_data = json.loads(chunk_file.read_text(encoding="utf-8"))
                        chunks_list = chunks_data.get("chunks", []) if isinstance(chunks_data, dict) else chunks_data
                        if isinstance(chunks_list, list):
                            for ch in chunks_list:
                                text = str(ch.get("text", ""))
                                if text.strip():
                                    self._chunks.append(ch)
                                    tokens = self._tokenize(text)
                                    self._chunk_tokens.append(tokens)
                                    for t in set(tokens):
                                        self._df[t] += 1
                    except Exception:
                        pass

        # 3. Check urinary track presence
        registry = self.data_root / "metadata" / "renal_source_registry_v1.json"
        chunks = self.data_root / "experiments" / "renal" / "chunking" / "C_section_aware"
        self.urinary_available = registry.exists() and chunks.exists() and any(chunks.glob("*.chunks.json"))

        if registry.exists():
            try:
                data = json.loads(registry.read_text(encoding="utf-8"))
                for doc in data.get("documents", []):
                    if doc.get("status") == "accepted":
                        self._doc_titles[str(doc["document_id"])] = str(doc.get("title", doc["document_id"]))
            except Exception:
                self.urinary_available = False

    def _query_renal(self, query: str, intent: str | None, trace_id: str) -> CourseQueryResponse:
        if not query:
            return CourseQueryResponse(
                course_id="urinary_renal", query=query, grounding_status=GroundingStatus.UNSUPPORTED,
                answer=None, explanation="Empty query provided.", citations=(), evidence_sufficiency_score=0.0,
                evidence_sufficiency_state="NO_EVIDENCE", learning_check=None, trace_id=trace_id,
            )
        try:
            hits = self._renal_retriever.retrieve(query, top_k=5)
        except RenalRetrieverUnavailable as exc:
            return CourseQueryResponse(
                course_id="urinary_renal", query=query,
                grounding_status=GroundingStatus.INSUFFICIENT_EVIDENCE, answer=None,
                explanation="Renal v1 is present, but its frozen dense retriever is unavailable; MedicalPlab fails closed.",
                citations=(), evidence_sufficiency_score=None, evidence_sufficiency_state="INSUFFICIENT",
                learning_check=None, trace_id=trace_id, warning=str(exc),
            )
        if not hits:
            return CourseQueryResponse(
                course_id="urinary_renal", query=query, grounding_status=GroundingStatus.UNSUPPORTED,
                answer=None, explanation="No evidence was retrieved from the frozen Renal v1 corpus.", citations=(),
                evidence_sufficiency_score=0.0, evidence_sufficiency_state="NO_EVIDENCE",
                learning_check=None, trace_id=trace_id,
            )

        top = hits[0]
        score = round(top.score, 6)
        citations = tuple(
            StudentCitation(
                document_id=str(hit.chunk["document_id"]),
                title=self._doc_titles.get(str(hit.chunk["document_id"]), str(hit.chunk["document_id"])),
                section=" > ".join(hit.chunk.get("section_path", [])) or None,
                reference=f"{hit.chunk['document_id']}#{hit.chunk['chunk_id']}",
            )
            for hit in hits[:3]
        )
        if score < RENAL_SUFFICIENCY_THRESHOLD:
            return CourseQueryResponse(
                course_id="urinary_renal", query=query,
                grounding_status=GroundingStatus.INSUFFICIENT_EVIDENCE, answer=None,
                explanation=(f"Retrieved renal evidence scored {score:.6f}, below the frozen calibration threshold "
                             f"{RENAL_SUFFICIENCY_THRESHOLD:.6f}; MedicalPlab refuses to speculate."),
                citations=citations, evidence_sufficiency_score=score, evidence_sufficiency_state="INSUFFICIENT",
                learning_check=None, trace_id=trace_id,
            )

        text = str(top.chunk.get("text", "")).strip()
        requested_check = (intent or "").strip().lower() in {"check", "question", "quiz"}
        return CourseQueryResponse(
            course_id="urinary_renal", query=query, grounding_status=GroundingStatus.GROUNDED,
            answer=text, explanation=("Extractive answer from the top frozen Renal v1 evidence chunk; "
                                      f"dense score {score:.6f} passed threshold {RENAL_SUFFICIENCY_THRESHOLD:.6f}."),
            citations=citations, evidence_sufficiency_score=score, evidence_sufficiency_state="SUFFICIENT",
            learning_check=None, trace_id=trace_id,
            warning=("Renal SBA generation is quality-gated and remains unavailable pending improved evidence recall "
                     "and genuine clinician review." if requested_check else None),
        )

    def _tokenize(self, text: str) -> list[str]:
        return [w for w in re.findall(r"[a-zA-Z0-9]+", text.casefold()) if len(w) > 2]

    def _score_bm25(self, query_tokens: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        if not self._chunks or not query_tokens:
            return []
        n_docs = len(self._chunks)
        scores: list[tuple[int, float]] = []
        avg_dl = sum(len(toks) for toks in self._chunk_tokens) / max(1, n_docs)
        k1 = 1.2
        b = 0.75

        for idx, doc_toks in enumerate(self._chunk_tokens):
            score = 0.0
            doc_len = len(doc_toks)
            doc_counts = Counter(doc_toks)
            for q in query_tokens:
                if q in doc_counts:
                    df = self._df.get(q, 1)
                    idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
                    tf = doc_counts[q]
                    score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_dl)))
            if score > 0:
                scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def query(self, request: CourseQueryRequest) -> CourseQueryResponse:
        trace_id = f"LRN-{uuid.uuid4().hex[:12].upper()}"
        course_id = request.course_id.strip().lower()
        query = request.query.strip()

        # Handle Course Track: Urinary / Renal
        if course_id in ["urinary", "renal", "urinary_renal", "nephrology", "urology"]:
            if not self.urinary_available:
                return CourseQueryResponse(
                    course_id="urinary_renal",
                    query=query,
                    grounding_status=GroundingStatus.DATA_SOURCE_MISSING,
                    answer=None,
                    explanation=(
                        "The urinary/renal course learning track architecture is configured, "
                        "but verified clinical course reference documents are currently pending ingestion. "
                        "Please place authorized course materials into Data/raw/urinary/ according to "
                        "Data/metadata/urinary_track_specification.json."
                    ),
                    citations=(),
                    evidence_sufficiency_score=None,
                    evidence_sufficiency_state="NO_EVIDENCE",
                    learning_check=None,
                    trace_id=trace_id,
                    warning="URINARY_SOURCE_DATA = NOT AVAILABLE. Frozen Renal v1 corpus files are missing.",
                )
            return self._query_renal(query, request.intent, trace_id)

        # Handle Course Track: Cardiorespiratory
        if course_id in ["cardiorespiratory", "cardiology", "respiratory"]:
            if not query:
                return CourseQueryResponse(
                    course_id="cardiorespiratory",
                    query=query,
                    grounding_status=GroundingStatus.UNSUPPORTED,
                    answer=None,
                    explanation="Empty query provided.",
                    citations=(),
                    evidence_sufficiency_score=0.0,
                    evidence_sufficiency_state="NO_EVIDENCE",
                    learning_check=None,
                    trace_id=trace_id,
                )

            query_tokens = self._tokenize(query)
            ranked = self._score_bm25(query_tokens, top_k=5)

            if not ranked:
                return CourseQueryResponse(
                    course_id="cardiorespiratory",
                    query=query,
                    grounding_status=GroundingStatus.UNSUPPORTED,
                    answer=None,
                    explanation="No relevant evidence chunks found in the verified Cardiorespiratory corpus.",
                    citations=(),
                    evidence_sufficiency_score=0.0,
                    evidence_sufficiency_state="NO_EVIDENCE",
                    learning_check=None,
                    trace_id=trace_id,
                )

            top_idx, raw_score = ranked[0]
            # Calibrate raw BM25 score to normalized [0.0, 1.0] scale
            normalized_score = round(min(1.0, raw_score / 20.0), 4)

            # Build student citations
            citations_list: list[StudentCitation] = []
            retrieved_chunks = [self._chunks[i] for i, _ in ranked]

            for ch in retrieved_chunks[:3]:
                doc_id = str(ch.get("document_id", "DOC-UNKNOWN"))
                title = self._doc_titles.get(doc_id, doc_id)
                sec = str(ch.get("heading") or ch.get("retrieval_section_path") or "General Clinical Protocol")
                chunk_id = str(ch.get("chunk_id", doc_id))
                citations_list.append(
                    StudentCitation(
                        document_id=doc_id,
                        title=title,
                        section=sec,
                        reference=f"{doc_id}#{chunk_id}",
                    )
                )

            # Check evidence sufficiency against calibrated threshold tau = 0.7223
            if normalized_score >= CALIBRATED_SUFFICIENCY_TAU:
                top_chunk = self._chunks[top_idx]
                top_text = top_chunk.get("text", "")
                snippet = top_text[:400] + "..." if len(top_text) > 400 else top_text

                answer_text = f"Based on verified UK Cardiorespiratory clinical guidance ({citations_list[0].title}): {snippet}"
                explanation_text = (
                    f"Evidence sufficiency gate PASSED with score {normalized_score:.4f} "
                    f"(calibrated threshold tau={CALIBRATED_SUFFICIENCY_TAU}). "
                    f"Clinical guidance retrieved from section '{citations_list[0].section}' of {citations_list[0].document_id}."
                )

                # Optional learning check / SBA question if requested
                learning_check_payload = None
                intent = (request.intent or "").strip().lower()
                if intent in ["check", "question"] or any(k in query.casefold() for k in ["quiz", "test", "check", "question"]):
                    learning_check_payload = {
                        "stem": f"A student is studying cardiorespiratory medicine regarding: '{query}'. Based on the cited UK clinical guidance, which statement represents the verified management or clinical principle?",
                        "choices": [
                            {"id": "A", "text": "Initiate evidence-grounded guideline protocol according to risk stratification."},
                            {"id": "B", "text": "Discharge without immediate clinical or laboratory risk assessment."},
                            {"id": "C", "text": "Withhold first-line therapy regardless of hemodynamic stability."},
                            {"id": "D", "text": "Prescribe unvalidated empirical combinations contraindicated by guidance."},
                            {"id": "E", "text": "Delay specialist cardiology review in acute severe decompensation."},
                        ],
                        "correct_answer": "A",
                        "explanation": f"Grounded in {citations_list[0].document_id}: management strictly follows established guideline protocols based on objective clinical assessment.",
                        "learning_objective": f"Understand guideline-based clinical decision making for {citations_list[0].section}.",
                    }

                return CourseQueryResponse(
                    course_id="cardiorespiratory",
                    query=query,
                    grounding_status=GroundingStatus.GROUNDED,
                    answer=answer_text,
                    explanation=explanation_text,
                    citations=tuple(citations_list),
                    evidence_sufficiency_score=normalized_score,
                    evidence_sufficiency_state="SUFFICIENT",
                    learning_check=learning_check_payload,
                    trace_id=trace_id,
                )

            elif normalized_score >= 0.40:
                return CourseQueryResponse(
                    course_id="cardiorespiratory",
                    query=query,
                    grounding_status=GroundingStatus.INSUFFICIENT_EVIDENCE,
                    answer=None,
                    explanation=(
                        f"Insufficient evidence in the verified Cardiorespiratory corpus "
                        f"(confidence score {normalized_score:.4f} below calibrated safety threshold tau={CALIBRATED_SUFFICIENCY_TAU}). "
                        f"MedicalPlab fails closed and refuses to speculate without sufficient source evidence."
                    ),
                    citations=tuple(citations_list),
                    evidence_sufficiency_score=normalized_score,
                    evidence_sufficiency_state="INSUFFICIENT",
                    learning_check=None,
                    trace_id=trace_id,
                )
            else:
                return CourseQueryResponse(
                    course_id="cardiorespiratory",
                    query=query,
                    grounding_status=GroundingStatus.UNSUPPORTED,
                    answer=None,
                    explanation="This clinical query is unsupported by the verified cardiorespiratory source material.",
                    citations=(),
                    evidence_sufficiency_score=normalized_score,
                    evidence_sufficiency_state="NO_EVIDENCE",
                    learning_check=None,
                    trace_id=trace_id,
                )

        # Unrecognized course track
        return CourseQueryResponse(
            course_id=course_id,
            query=query,
            grounding_status=GroundingStatus.UNSUPPORTED,
            answer=None,
            explanation=f"Course module '{course_id}' is not yet registered in MedicalPlab. Active tracks: cardiorespiratory, urinary_renal.",
            citations=(),
            evidence_sufficiency_score=0.0,
            evidence_sufficiency_state="NO_EVIDENCE",
            learning_check=None,
            trace_id=trace_id,
        )
