"""Main service orchestrator for the Grounded Generative Tutor."""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

from medicalplab.evidence_engine.models import RetrievedCandidate
from medicalplab.evidence_engine.service import SharedEvidenceEngineV2
from medicalplab.tutor.claim_segmenter import PropositionSegmenter
from medicalplab.tutor.forensics import ForensicAuditLogger
from medicalplab.tutor.leak_scanner import AnswerLeakScanner
from medicalplab.tutor.models import (
    DistractorItem,
    LatencyBreakdownDTO,
    PedagogicalState,
    TutorChatRequest,
    TutorChatResponse,
    TutorCitationDTO,
    TutorDraftOutput,
    TutorVerificationSummaryDTO,
)
from medicalplab.tutor.prompts import (
    TUTOR_RESPONSE_JSON_SCHEMA,
    TUTOR_SYSTEM_PROMPT,
    build_evidence_context,
    build_history_context,
    build_question_context,
    build_user_prompt,
)
from medicalplab.tutor.provider import GenerativeProvider, get_default_provider
from medicalplab.tutor.rights import SourceRightsGate
from medicalplab.tutor.session import TutorSessionManager, verify_submission_proof
from medicalplab.tutor.telemetry import TutorTelemetryEvent, TutorTelemetryLogger
from medicalplab.tutor.verifier import TutorPostVerifier

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[3]
BANK_FILE = ROOT_DIR / "Data/university/questions.json"


class TutorService:
    """Orchestrates evidence retrieval, rights gating, generation, verification, and leakage protection."""

    def __init__(
        self,
        engine: SharedEvidenceEngineV2 | None = None,
        provider: GenerativeProvider | None = None,
        rights_gate: SourceRightsGate | None = None,
        post_verifier: TutorPostVerifier | None = None,
        segmenter: PropositionSegmenter | None = None,
        leak_scanner: AnswerLeakScanner | None = None,
        session_manager: TutorSessionManager | None = None,
        telemetry: TutorTelemetryLogger | None = None,
        forensics: ForensicAuditLogger | None = None,
        questions_path: Path | str | None = None,
    ) -> None:
        self.engine = engine or SharedEvidenceEngineV2(data_root=ROOT_DIR / "Data")
        self.provider = provider or get_default_provider()
        self.rights_gate = rights_gate or SourceRightsGate()
        self.post_verifier = post_verifier or TutorPostVerifier(claim_verifier=self.engine.verifier)
        self.segmenter = segmenter or PropositionSegmenter()
        self.leak_scanner = leak_scanner or AnswerLeakScanner()
        self.session_manager = session_manager or TutorSessionManager()
        self.telemetry = telemetry or TutorTelemetryLogger()
        # store_full_text=True: this pass targets synthetic/test evaluation traffic only (no PII).
        self.forensics = forensics or ForensicAuditLogger(store_full_text=True)

        self._questions: dict[str, dict[str, Any]] = {}
        self._load_questions(questions_path or BANK_FILE)

    def _load_questions(self, path: Path | str) -> None:
        p = Path(path)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for q in data:
                        if isinstance(q, dict) and "id" in q:
                            self._questions[q["id"]] = q
            except Exception as exc:
                logger.warning(f"Failed to load university questions: {exc}")

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        return self._questions.get(question_id)

    def _build_safe_fallback(
        self,
        state: PedagogicalState,
        question: dict[str, Any] | None,
        topic: str | None,
        query: str,
        reason: str,
    ) -> dict[str, Any]:
        """Construct safe pedagogical fallback when generation fails, leaks, or is unverified."""
        topic_name = topic or (question.get("topic") if question else "Renal Physiology")

        if state in ("PRE_SUBMISSION", "GENERAL_STUDY"):
            # Never dump raw retrieved passages or question answers in pre-submission or general study fallback.
            # This fallback is served with zero citations, so it can never satisfy SUPPORTED_BY_EVIDENCE.
            # It must therefore contain ZERO substantive medical/basic-science factual claims of its own -
            # every sentence here must remain purely procedural/content-neutral, regardless of topic_name.
            return {
                "message": (
                    "I couldn't verify enough evidence to give a fully grounded explanation right now. "
                    "Let's work through this together using what you already know."
                ),
                "socratic_question": "What do you already know that might help you approach this question?",
                "hints": [
                    "Level 1: Try identifying the main concept the question is testing.",
                    "Level 2: Compare each option against what you have already studied, and rule out the ones that do not fit.",
                ],
                "misconception": None,
                "mechanistic_explanation": None,
                "distractor_analysis": None,
                "revision_summary": "Revisit your course material on this topic to confirm the relevant concept before moving on.",
                "citations": [],
            }
        else:
            # In post-submission, static verified explanation can safely be provided
            expl = question.get("explanation") if question else "Review the core verified mechanism in your reference text."
            ev_excerpt = question.get("evidence", {}).get("excerpt") if question else None
            return {
                "message": f"Post-submission review for {topic_name}: {expl}",
                "socratic_question": None,
                "hints": None,
                "misconception": None,
                "mechanistic_explanation": ev_excerpt,
                "distractor_analysis": None,
                "revision_summary": expl,
                "citations": [],
            }

    def chat(
        self,
        request: TutorChatRequest,
        x_user_id: str | None = None,
    ) -> TutorChatResponse:
        """Handle an evidence-grounded tutor dialogue turn."""
        t_start = time.perf_counter()
        req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

        # 1. Identity & Submission State Proof
        # X-User-Id is classified as anonymous/demo learner identity, NOT authentication.
        # PRE_SUBMISSION is always the default.
        server_user_id = (x_user_id or request.learner_id or "anonymous_device").strip()
        question = self.get_question(request.question_id) if request.question_id else None

        pedagogical_state: PedagogicalState = verify_submission_proof(
            user_id=x_user_id,
            question_id=request.question_id,
            attempt_key=request.attempt_key,
        )

        session = self.session_manager.get_or_create(request.session_id, user_id=server_user_id)

        # 2. Evidence Retrieval
        t_retrieval_start = time.perf_counter()
        packet = self.engine.query(
            query=request.query,
            mode="TUTOR",
            top_candidates=50,
            rerank_top_k=25,
        )
        retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000.0

        # Check retrieval abstention: real failure if no candidates, source/confidence failure,
        # or if an explicit out-of-scope topic is requested (Phase 1 is strictly Preclinical Renal)
        is_out_of_scope_topic = bool(
            request.topic
            and not any(r in request.topic.lower() for r in ["renal", "kidney", "nephro", "glomerul", "raas", "fluid", "acid-base", "general", "physiology"])
        )
        real_retrieval_failure = (
            not packet.candidates
            or packet.abstain_reason in {"NO_CANDIDATES_RETRIEVED", "INELIGIBLE_EVIDENCE_SOURCE", "LOW_RETRIEVAL_CONFIDENCE"}
            or is_out_of_scope_topic
        )
        if real_retrieval_failure:
            abstain_reason = "OUT_OF_SCOPE_TOPIC" if is_out_of_scope_topic else (packet.abstain_reason or "INSUFFICIENT_RETRIEVAL_SUPPORT")
            total_ms = (time.perf_counter() - t_start) * 1000.0
            telem_event = TutorTelemetryEvent(
                request_id=req_id,
                session_id=session.session_id,
                learner_id=server_user_id,
                question_id=request.question_id,
                topic=request.topic or (question.get("topic") if question else "General"),
                pedagogical_state=pedagogical_state,
                mode=request.mode,
                evidence_status="ABSTAIN",
                abstain_reason=abstain_reason,
                provider=self.provider.provider_name,
                model=self.provider.model_name,
                requested_model=self.provider.model_name,
                latency_retrieval_ms=round(retrieval_ms, 2),
                latency_total_ms=round(total_ms, 2),
                fallback_applied=False,
            )
            self.telemetry.log_event(telem_event)

            return TutorChatResponse(
                response_id=req_id,
                session_id=session.session_id,
                mode=request.mode,
                message=(
                    f"I must abstain from tutoring on this specific query. "
                    f"No verified basic-science evidence was retrieved from the open-access renal corpus "
                    f"(reason: {abstain_reason})."
                ),
                abstain=True,
                abstain_reason=abstain_reason,
                support_status="ABSTAIN",
                fallback_applied=False,
                pedagogical_state=pedagogical_state,
                provider=self.provider.provider_name,
                model=self.provider.model_name,
                requested_provider=self.provider.provider_name,
                requested_model=self.provider.model_name,
                actual_generation_provider=self.provider.provider_name,
                actual_generation_model=self.provider.model_name,
                latency_breakdown=LatencyBreakdownDTO(
                    retrieval_ms=round(retrieval_ms, 2),
                    total_ms=round(total_ms, 2),
                ),
                verification=TutorVerificationSummaryDTO(),
            )

        # 3. Source Rights Gate
        allowed_candidates = self.rights_gate.filter_candidates(packet.candidates)
        if not allowed_candidates:
            total_ms = (time.perf_counter() - t_start) * 1000.0
            telem_event = TutorTelemetryEvent(
                request_id=req_id,
                session_id=session.session_id,
                learner_id=server_user_id,
                question_id=request.question_id,
                topic=request.topic or "General",
                pedagogical_state=pedagogical_state,
                mode=request.mode,
                evidence_status="ABSTAIN",
                abstain_reason="SOURCE_RIGHTS_NOT_ALLOWED",
                provider=self.provider.provider_name,
                model=self.provider.model_name,
                requested_model=self.provider.model_name,
                latency_retrieval_ms=round(retrieval_ms, 2),
                latency_total_ms=round(total_ms, 2),
            )
            self.telemetry.log_event(telem_event)

            return TutorChatResponse(
                response_id=req_id,
                session_id=session.session_id,
                mode=request.mode,
                message="Retrieved sources cannot enter generative prompts under licensing policy (AI_REUSE_REQUIRES_PERMISSION).",
                abstain=True,
                abstain_reason="SOURCE_RIGHTS_NOT_ALLOWED",
                support_status="ABSTAIN",
                pedagogical_state=pedagogical_state,
                provider=self.provider.provider_name,
                model=self.provider.model_name,
                requested_provider=self.provider.provider_name,
                requested_model=self.provider.model_name,
                actual_generation_provider=self.provider.provider_name,
                actual_generation_model=self.provider.model_name,
                latency_breakdown=LatencyBreakdownDTO(
                    retrieval_ms=round(retrieval_ms, 2),
                    total_ms=round(total_ms, 2),
                ),
            )

        # 4. Context & Prompt Assembly
        # Ensure question's verified evidence chunk is included if available
        if question and "evidence" in question:
            q_ev = question["evidence"]
            q_cid = q_ev.get("chunk_id")
            if q_cid and q_cid in self.engine.retriever.chunks:
                if not any(c.chunk_id == q_cid for c in allowed_candidates):
                    c_data = self.engine.retriever.chunks[q_cid]
                    q_cand = RetrievedCandidate(
                        chunk_id=q_cid,
                        document_id=c_data.get("document_id", q_ev.get("document_id")),
                        heading=c_data.get("heading", ""),
                        section_path=c_data.get("section_path", []),
                        text=c_data.get("text", q_ev.get("excerpt", "")),
                        doc_title=c_data.get("doc_title", q_ev.get("title", "")),
                        fused_score=1.0,
                    )
                    allowed_candidates.insert(0, q_cand)
        evidence_xml = build_evidence_context(allowed_candidates[:5])
        question_xml = (
            build_question_context(question, pedagogical_state, request.selected_option)
            if question
            else None
        )
        history_xml = build_history_context(session.history)
        user_prompt = build_user_prompt(
            query=request.query,
            evidence_xml=evidence_xml,
            question_xml=question_xml,
            history_xml=history_xml,
            mode=request.mode,
            hint_level=request.hint_level,
        )

        # 5. Generative Provider Call
        t_gen_start = time.perf_counter()
        provider_resp = None
        generation_error = None

        try:
            provider_resp = self.provider.generate_structured(
                system_prompt=TUTOR_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_schema=TUTOR_RESPONSE_JSON_SCHEMA,
                temperature=0.0,
                max_tokens=3000,
            )
        except Exception as exc:
            logger.error(f"GenerativeProvider error: {exc}")
            generation_error = str(exc)

        generation_ms = (time.perf_counter() - t_gen_start) * 1000.0

        # Provider/model attribution: `provider_resp` (when present) reflects what ACTUALLY ran
        # this turn, which may differ from the requested/configured provider/model after an
        # automatic failover (e.g. requested gemini-3.8-flash -> actual gemini-3.5-flash). A
        # fallback model must never silently masquerade as the primary one in reporting.
        requested_provider_name = self.provider.provider_name
        requested_model_name = self.provider.model_name
        actual_provider_name = (
            provider_resp.provider if provider_resp and provider_resp.provider else requested_provider_name
        )
        actual_model_name = (
            provider_resp.model if provider_resp and provider_resp.model else requested_model_name
        )
        provider_failover_applied = bool(provider_resp and provider_resp.provider_failover_applied)
        primary_provider_error = provider_resp.primary_provider_error if provider_resp else generation_error

        # Handle Generation Failure or malformed output
        draft_dict: dict[str, Any] | None = None
        if provider_resp and provider_resp.structured_data:
            draft_dict = provider_resp.structured_data
        elif provider_resp and provider_resp.raw_text:
            try:
                draft_dict = json.loads(provider_resp.raw_text)
            except Exception:
                draft_dict = None

        fallback_applied = False
        if not draft_dict:
            fallback_applied = True
            draft_dict = self._build_safe_fallback(
                state=pedagogical_state,
                question=question,
                topic=request.topic,
                query=request.query,
                reason=generation_error or "MALFORMED_STRUCTURED_OUTPUT",
            )

        # 6. Post-Generation Verification
        t_verify_start = time.perf_counter()
        citations_raw = draft_dict.get("citations", [])

        # Check safety vetoes
        safety_vetoes = self.post_verifier.check_clinical_safety(draft_dict)

        # Check citation provenance if not in fallback
        prov_ok, prov_err = (True, None)
        if not fallback_applied and citations_raw:
            prov_ok, prov_err = self.post_verifier.validate_provenance(citations_raw, allowed_candidates)

        # Proposition extraction and verification
        props = self.segmenter.segment_all_fields(draft_dict)
        verif_summary, all_props_supported = self.post_verifier.verify_propositions(props, allowed_candidates)

        if safety_vetoes:
            verif_summary.veto_flags.extend(safety_vetoes)

        post_verify_ms = (time.perf_counter() - t_verify_start) * 1000.0

        # 7. Answer Leakage Scan for PRE_SUBMISSION
        leak_detected = False
        leak_reason = None
        if pedagogical_state == "PRE_SUBMISSION" and question:
            leak_detected, leak_reason = self.leak_scanner.scan_for_leaks(draft_dict, question)

        # Determine if fail-closed fallback must be applied
        needs_fallback = (
            safety_vetoes
            or not prov_ok
            or not all_props_supported
            or leak_detected
        )

        draft_verification_summary: TutorVerificationSummaryDTO | None = None

        if needs_fallback and not fallback_applied:
            fail_reason = (
                f"VETOES: {safety_vetoes}" if safety_vetoes
                else f"PROVENANCE_FAIL: {prov_err}" if not prov_ok
                else f"UNSUPPORTED_PROPOSITIONS ({verif_summary.unsupported_propositions})" if not all_props_supported
                else f"LEAK_DETECTED: {leak_reason}"
            )

            # Preserve the REJECTED draft's own verification result separately. It must never
            # be conflated with what is actually served to the learner (see served recompute below).
            draft_verification_summary = verif_summary

            fallback_applied = True
            draft_dict = self._build_safe_fallback(
                state=pedagogical_state,
                question=question,
                topic=request.topic,
                query=request.query,
                reason=fail_reason,
            )

            # Recompute verification against the ACTUAL served fallback content - never reuse
            # rejected-draft proposition counts as if they described what the learner sees.
            served_props = self.segmenter.segment_all_fields(draft_dict)
            verif_summary, _ = self.post_verifier.verify_propositions(served_props, allowed_candidates)

        total_ms = (time.perf_counter() - t_start) * 1000.0

        # 8. Build Citations DTO
        citation_dtos: list[TutorCitationDTO] = []
        if not fallback_applied:
            for c in citations_raw:
                doc_id = c.get("document_id", "")
                rights_info = self.rights_gate._doc_rights.get(doc_id, {})
                citation_dtos.append(
                    TutorCitationDTO(
                        ref=c.get("ref", doc_id),
                        quote=c.get("quote", ""),
                        document_id=doc_id,
                        pmcid=rights_info.get("pmcid"),
                        title=rights_info.get("title", doc_id),
                        license=rights_info.get("license", "CC BY"),
                        chunk_id=c.get("chunk_id", ""),
                    )
                )

        # Distractor analysis DTOs (post-submission only)
        distractor_dtos = None
        raw_distractors = draft_dict.get("distractor_analysis")
        if pedagogical_state == "POST_SUBMISSION" and raw_distractors and isinstance(raw_distractors, list):
            distractor_dtos = []
            for d in raw_distractors:
                if isinstance(d, dict):
                    distractor_dtos.append(
                        DistractorItem(
                            option=d.get("option", ""),
                            text=d.get("text", ""),
                            why_incorrect=d.get("why_incorrect", ""),
                            supported_by_ref=d.get("supported_by_ref", ""),
                        )
                    )

        # 9. Update Session Turns
        session.add_turn("user", request.query, max_turns=request.max_context_turns)
        session.add_turn("tutor", draft_dict.get("message", ""), max_turns=request.max_context_turns)

        # 10. Telemetry Logging
        in_tokens = provider_resp.input_tokens if provider_resp else 0
        out_tokens = provider_resp.output_tokens if provider_resp else 0
        cost = self.telemetry.calculate_cost(actual_provider_name, in_tokens, out_tokens)

        # Forensic audit capture (non-sensitive): records, per SUBSTANTIVE_FACTUAL proposition
        # from the originally generated draft, the evidence candidate actually evaluated and the
        # raw verifier result - independent of whatever ended up served. `reached_learner` is
        # forced False whenever fallback_applied is True (a veto/rejection always prevents the
        # draft's own propositions from reaching the learner).
        self.forensics.capture_propositions(
            request_id=req_id,
            propositions=props,
            candidates=allowed_candidates,
            rights_gate=self.rights_gate,
            requested_provider=requested_provider_name,
            requested_model=requested_model_name,
            actual_generation_provider=actual_provider_name,
            actual_generation_model=actual_model_name,
            provider_failover_applied=provider_failover_applied,
            support_status="SUPPORTED" if not fallback_applied else "SAFE_FALLBACK",
            reached_learner=not fallback_applied,
        )

        telem_event = TutorTelemetryEvent(
            request_id=req_id,
            session_id=session.session_id,
            learner_id=server_user_id,
            question_id=request.question_id,
            topic=request.topic or (question.get("topic") if question else "General"),
            pedagogical_state=pedagogical_state,
            mode=request.mode,
            evidence_status="SUPPORTED" if not fallback_applied else "FALLBACK",
            provider=actual_provider_name,
            model=actual_model_name,
            requested_model=requested_model_name,
            provider_failover_applied=provider_failover_applied,
            primary_provider_error=primary_provider_error,
            latency_retrieval_ms=round(retrieval_ms, 2),
            latency_generation_ms=round(generation_ms, 2),
            latency_post_verify_ms=round(post_verify_ms, 2),
            latency_total_ms=round(total_ms, 2),
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            estimated_cost_usd=cost,
            propositions_total=verif_summary.total_propositions,
            propositions_supported=verif_summary.supported_propositions,
            propositions_unsupported=verif_summary.unsupported_propositions,
            fallback_applied=fallback_applied,
        )
        self.telemetry.log_event(telem_event)

        return TutorChatResponse(
            response_id=req_id,
            session_id=session.session_id,
            mode=request.mode,
            message=draft_dict.get("message", ""),
            socratic_question=draft_dict.get("socratic_question"),
            hints=draft_dict.get("hints"),
            misconception=draft_dict.get("misconception"),
            mechanistic_explanation=draft_dict.get("mechanistic_explanation"),
            distractor_analysis=distractor_dtos,
            revision_summary=draft_dict.get("revision_summary"),
            citations=citation_dtos,
            evidence_packet_id=f"EP-{req_id}",
            support_status="SUPPORTED" if not fallback_applied else "SAFE_FALLBACK",
            abstain=False,
            fallback_applied=fallback_applied,
            pedagogical_state=pedagogical_state,
            provider=actual_provider_name,
            model=actual_model_name,
            requested_provider=requested_provider_name,
            requested_model=requested_model_name,
            actual_generation_provider=actual_provider_name,
            actual_generation_model=actual_model_name,
            provider_failover_applied=provider_failover_applied,
            primary_provider_error=primary_provider_error,
            latency_breakdown=LatencyBreakdownDTO(
                retrieval_ms=round(retrieval_ms, 2),
                generation_ms=round(generation_ms, 2),
                post_verify_ms=round(post_verify_ms, 2),
                total_ms=round(total_ms, 2),
            ),
            verification=verif_summary,
            draft_verification=draft_verification_summary,
        )
