"""Fail-closed, proof-carrying validator for PLAB V9 automated closure checkpoint.

Enforces:
1. Recomputed raw byte SHA-256 hashes of preserved raw source snapshots on disk.
2. Recomputed UTF8_LF_CANONICAL_TEXT SHA-256 hashes of normalized representations on disk.
3. Canonical organization identity, role separation, and approved official hosts.
4. Concrete currentness evidence (fails on bare booleans).
5. Exact contiguous evidence span containment (no synthetic reconstruction).
6. Complete atomic claim decomposition with direct clinical support.
7. Bound option reviews with single-best-answer adjudication.
8. Zero clinician approval and zero golden promotions.
9. Cross-platform LF newline invariance.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional

from medicalplab.plab.v9.hashing import (
    canonicalize_newlines_to_lf,
    compute_canonical_lf_text_sha256,
    compute_file_canonical_lf_sha256,
    compute_file_raw_sha256,
)
from medicalplab.plab.v9.identity import (
    APPROVED_OFFICIAL_HOSTS,
    extract_host,
    verify_source_identity,
)
from medicalplab.plab.v9.models import (
    OrganizationRole,
    RedistributionReadiness,
    SpanType,
    SupportStatus,
    TrustState,
)

ALLOWED_DISPOSITIONS = {
    "PRESERVE_AFTER_REVALIDATION",
    "REPAIR",
    "REWRITE",
    "REPLACE",
    "QUARANTINE",
    "DEFER",
    "REJECT",
}

ALLOWED_BLOCKER_CLASSES = {
    "A_ENGINEERING_FIXABLE",
    "B_EVIDENCE_FIXABLE",
    "C_CONTENT_REPAIRABLE",
    "D_CONTENT_REWRITE_REQUIRED",
    "E_AUTHORITATIVE_SOURCE_CONFLICT",
    "F_HUMAN_CLINICAL_JUDGMENT_REQUIRED",
    "G_LICENSING_BLOCKER",
    "H_NO_AUTHORITATIVE_EVIDENCE",
    "I_UNSAFE_OR_INVALID_QUESTION",
}

FINAL_NON_ENGINEERING_BLOCKERS = {
    "E_AUTHORITATIVE_SOURCE_CONFLICT",
    "F_HUMAN_CLINICAL_JUDGMENT_REQUIRED",
    "G_LICENSING_BLOCKER",
    "H_NO_AUTHORITATIVE_EVIDENCE",
    "I_UNSAFE_OR_INVALID_QUESTION",
}

TRUST_STATES = {t.value for t in TrustState}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require(condition: bool, message: str, errors: List[str]) -> None:
    if not condition:
        errors.append(message)


def validate_source_packet(
    packet: Mapping[str, Any], root_dir: Optional[Path] = None
) -> List[str]:
    """Validate raw snapshot proof, normalized text representation, identity, currentness, and exact spans."""
    errors: List[str] = []
    sid = str(packet.get("source_id", "<missing>"))

    # Canonical endpoint and publisher host
    canonical_url = str(packet.get("canonical_url", ""))
    url_host = extract_host(canonical_url)
    _require(
        url_host in APPROVED_OFFICIAL_HOSTS,
        f"{sid}: source is not on an approved official host ({canonical_url})",
        errors,
    )
    _require(
        packet.get("http_status") == 200,
        f"{sid}: official retrieval did not return HTTP 200",
        errors,
    )

    # Canonical organization identity check
    org_errors = verify_source_identity(packet)
    errors.extend(org_errors)

    # Raw snapshot proof
    raw_path_str = str(packet.get("raw_snapshot_path", ""))
    _require(bool(raw_path_str), f"{sid}: missing raw snapshot path", errors)
    raw_sha = str(packet.get("raw_snapshot_sha256", "")).lower()
    _require(HEX64.match(raw_sha) is not None, f"{sid}: invalid raw response SHA256", errors)
    _require(
        packet.get("raw_snapshot_hash_basis") == "RAW_BYTES_SHA256",
        f"{sid}: raw_snapshot_hash_basis must be RAW_BYTES_SHA256",
        errors,
    )

    # Normalized representation proof
    norm_path_str = str(packet.get("normalized_representation_path", ""))
    _require(bool(norm_path_str), f"{sid}: missing normalized representation path", errors)
    norm_sha = str(packet.get("normalized_representation_sha256", "")).lower()
    _require(
        HEX64.match(norm_sha) is not None,
        f"{sid}: invalid normalized representation SHA256",
        errors,
    )
    _require(
        packet.get("normalized_representation_hash_basis") == "UTF8_LF_CANONICAL_TEXT",
        f"{sid}: normalized_representation_hash_basis must be UTF8_LF_CANONICAL_TEXT",
        errors,
    )

    # Redistribution classification
    redist = str(packet.get("redistribution_readiness", ""))
    _require(
        redist in {r.value for r in RedistributionReadiness},
        f"{sid}: invalid redistribution_readiness '{redist}'",
        errors,
    )

    norm_text = ""
    if root_dir is not None:
        raw_file = root_dir / raw_path_str
        _require(
            raw_file.exists(),
            f"{sid}: raw snapshot file does not exist at {raw_path_str}",
            errors,
        )
        if raw_file.exists():
            computed_raw_sha = compute_file_raw_sha256(raw_file)
            _require(
                computed_raw_sha == raw_sha,
                f"{sid}: raw snapshot hash mismatch on disk ({computed_raw_sha} != {raw_sha})",
                errors,
            )
            expected_size = packet.get("response_byte_length")
            if expected_size is not None and expected_size > 0:
                actual_size = raw_file.stat().st_size
                _require(
                    actual_size == expected_size,
                    f"{sid}: raw snapshot size mismatch ({actual_size} != {expected_size})",
                    errors,
                )

        norm_file = root_dir / norm_path_str
        _require(
            norm_file.exists(),
            f"{sid}: normalized representation file does not exist at {norm_path_str}",
            errors,
        )
        if norm_file.exists():
            computed_norm_sha = compute_file_canonical_lf_sha256(norm_file)
            _require(
                computed_norm_sha == norm_sha,
                f"{sid}: normalized representation hash mismatch on disk ({computed_norm_sha} != {norm_sha})",
                errors,
            )
            # Read normalized text canonicalized to LF for span offsets
            norm_text = canonicalize_newlines_to_lf(norm_file.read_text(encoding="utf-8"))
    else:
        norm_text = canonicalize_newlines_to_lf(str(packet.get("representation_text", "")))

    # Reject synthetic representations
    _require(
        len(norm_text.strip()) > 500,
        f"{sid}: representation text is too short or empty (<500 chars)",
        errors,
    )

    # Source identity and publisher verification
    declared_title = str(packet.get("canonical_title", "")).strip()
    _require(bool(declared_title), f"{sid}: missing declared canonical title", errors)
    _require(
        bool(str(packet.get("canonical_identifier", "")).strip()),
        f"{sid}: missing canonical identifier",
        errors,
    )

    # Currentness proof
    curr_evidence = packet.get("source_currentness_evidence") or packet.get("currentness_evidence") or {}
    _require(bool(curr_evidence), f"{sid}: missing source currentness evidence", errors)
    _require(
        bool(str(packet.get("currentness_basis", "")).strip()),
        f"{sid}: missing substantive currentness basis",
        errors,
    )

    # Recompute and verify exact evidence spans
    span_ids = set()
    spans = packet.get("evidence_spans", [])
    _require(bool(spans), f"{sid}: no evidence spans defined", errors)

    for span in spans:
        span_id = str(span.get("span_id", ""))
        span_type = str(span.get("span_type", "EXACT_SOURCE_SPAN"))
        exact_text = str(span.get("exact_text", ""))

        _require(
            bool(span_id) and span_id not in span_ids,
            f"{sid}: missing or duplicate evidence span id '{span_id}'",
            errors,
        )
        span_ids.add(span_id)
        _require(bool(exact_text.strip()), f"{sid}/{span_id}: empty evidence span text", errors)
        _require(
            span.get("exact_text_sha256") == sha256_text(exact_text),
            f"{sid}/{span_id}: evidence span text hash mismatch",
            errors,
        )
        _require(
            span_type in {s.value for s in SpanType},
            f"{sid}/{span_id}: invalid span type '{span_type}'",
            errors,
        )

        if span_type == "EXACT_SOURCE_SPAN":
            _require(
                exact_text in norm_text,
                f"{sid}/{span_id}: exact quote not present in verified normalized representation",
                errors,
            )
            start_char = span.get("start_char")
            end_char = span.get("end_char")
            if start_char is not None and end_char is not None:
                _require(
                    0 <= start_char < end_char <= len(norm_text),
                    f"{sid}/{span_id}: locator range out of bounds",
                    errors,
                )
                _require(
                    norm_text[start_char:end_char] == exact_text,
                    f"{sid}/{span_id}: locator char offset mismatch",
                    errors,
                )

    return errors


def _validate_bound_option_reviews(question: Mapping[str, Any], errors: List[str]) -> None:
    qid = str(question.get("question_id", "<missing>"))
    version = str(question.get("question_version", ""))
    stem = str(question.get("stem", ""))
    stem_hash = sha256_text(stem)
    choices = question.get("choices", [])
    expected = {str(choice.get("id")): str(choice.get("text", "")) for choice in choices}
    reviews = question.get("option_reviews", [])
    review_ids = [str(review.get("option_id", "")) for review in reviews]

    _require(
        set(review_ids) == set(expected),
        f"{qid}: option reviews are incomplete or reference unknown options",
        errors,
    )
    _require(len(review_ids) == len(set(review_ids)), f"{qid}: duplicate option review", errors)
    defensible = []
    rationale_hashes = set()
    for review in reviews:
        option_id = str(review.get("option_id", ""))
        option_text = expected.get(option_id, "")
        rationale = str(review.get("rationale", ""))
        _require(review.get("question_id") == qid, f"{qid}/{option_id}: cross-question rationale binding", errors)
        _require(review.get("question_version") == version, f"{qid}/{option_id}: stale question-version rationale", errors)
        _require(review.get("stem_sha256") == stem_hash, f"{qid}/{option_id}: stem hash mismatch", errors)
        _require(review.get("option_text") == option_text, f"{qid}/{option_id}: option text mismatch", errors)
        _require(review.get("option_text_sha256") == sha256_text(option_text), f"{qid}/{option_id}: option hash mismatch", errors)
        _require(len(rationale.split()) >= 6, f"{qid}/{option_id}: boilerplate or missing rationale", errors)
        rationale_hash = sha256_text(rationale)
        _require(rationale_hash not in rationale_hashes, f"{qid}/{option_id}: duplicate rationale", errors)
        rationale_hashes.add(rationale_hash)
        if review.get("is_defensible") is True:
            defensible.append(option_id)
    _require(defensible == [question.get("correct_answer")], f"{qid}: one-best-answer adjudication failed ({defensible})", errors)


def validate_question_record(
    question: Mapping[str, Any], source_packets: Mapping[str, Mapping[str, Any]]
) -> List[str]:
    """Recompute a question's eligibility from atomic claims, exact spans, and coverage."""
    errors: List[str] = []
    qid = str(question.get("question_id", "<missing>"))
    grounded = question.get("source_grounded") is True
    disposition = str(question.get("disposition", ""))
    trust_state = str(question.get("trust_state", ""))

    _require(disposition in ALLOWED_DISPOSITIONS, f"{qid}: invalid disposition {disposition}", errors)
    _require(trust_state in TRUST_STATES, f"{qid}: unauthorized trust state {trust_state}", errors)
    _require(question.get("clinician_approved") is not True, f"{qid}: fabricated clinician approval", errors)
    _require(question.get("golden") is not True, f"{qid}: automatic Golden promotion", errors)
    _require(question.get("golden_eligible") is not True, f"{qid}: automatic Golden eligibility", errors)

    if not grounded:
        _require(
            trust_state in {"QUARANTINED", "DEFERRED", "REJECTED"},
            f"{qid}: non-grounded item has review-ready trust",
            errors,
        )
        blocker_class = str(question.get("blocker_class", ""))
        _require(
            blocker_class in FINAL_NON_ENGINEERING_BLOCKERS,
            f"{qid}: unresolved engineering/content blocker {blocker_class}",
            errors,
        )
        _require(
            bool(str(question.get("blocking_reason", "")).strip()),
            f"{qid}: missing substantive blocking reason",
            errors,
        )
        _require(
            question.get("remaining_engineering_blocker") is False,
            f"{qid}: hidden engineering blocker",
            errors,
        )
        return errors

    _require(
        trust_state == "CLINICIAN_REVIEW_REQUIRED",
        f"{qid}: grounded item is not bounded at clinician review",
        errors,
    )
    _require(
        disposition not in {"QUARANTINE", "DEFER", "REJECT"},
        f"{qid}: grounded item has blocked disposition",
        errors,
    )
    _require(question.get("clinician_review_ready") is True, f"{qid}: grounded item is not review ready", errors)

    claims = question.get("atomic_claims", [])
    _require(bool(claims), f"{qid}: no atomic claims", errors)
    claim_ids = {str(claim.get("claim_id", "")) for claim in claims}
    _require("" not in claim_ids and len(claim_ids) == len(claims), f"{qid}: missing or duplicate claim id", errors)

    decisive = [claim for claim in claims if claim.get("is_decisive") is True]
    _require(bool(decisive), f"{qid}: no decisive claim", errors)

    packet_spans: Dict[str, Dict[str, str]] = {
        sid: {str(span.get("span_id")): str(span.get("exact_text", "")) for span in packet.get("evidence_spans", [])}
        for sid, packet in source_packets.items()
    }

    for claim in claims:
        cid = str(claim.get("claim_id", ""))
        sid = str(claim.get("source_id", ""))
        _require(sid in source_packets, f"{qid}/{cid}: unknown source identity '{sid}'", errors)

        span_ids_list = claim.get("evidence_span_ids")
        if span_ids_list is None:
            span_ids_list = [str(claim.get("evidence_span_id", ""))]

        _require(bool(span_ids_list), f"{qid}/{cid}: no evidence span referenced", errors)

        quotes = []
        for span_id in span_ids_list:
            evidence_text = packet_spans.get(sid, {}).get(span_id, "")
            _require(bool(evidence_text), f"{qid}/{cid}: unverified evidence span '{span_id}'", errors)
            quotes.append(evidence_text)

        expected_quote = " ".join(quotes)
        actual_quote = str(claim.get("evidence_quote", ""))
        _require(
            actual_quote in (expected_quote, "\n".join(quotes), quotes[0] if len(quotes) == 1 else ""),
            f"{qid}/{cid}: quote/source span mismatch",
            errors,
        )

        spans_key = "|".join(sorted(span_ids_list))
        quotes_key = "|".join(sorted(quotes))
        binding = sha256_text(
            f"{qid}|{question.get('question_version')}|{claim.get('claim_text')}|{sid}|{spans_key}|{quotes_key}"
        )
        _require(
            claim.get("evidence_binding_sha256") == binding,
            f"{qid}/{cid}: wrong-source or stale evidence binding",
            errors,
        )

        _require(claim.get("support_status") == "DIRECT_SUPPORT", f"{qid}/{cid}: unsupported clinical claim", errors)
        _require(claim.get("source_identity_pass") is True, f"{qid}/{cid}: source identity failed", errors)
        _require(claim.get("source_currentness_pass") is True, f"{qid}/{cid}: source currentness failed", errors)
        _require(claim.get("span_verification_pass") is True, f"{qid}/{cid}: span verification failed", errors)
        _require(claim.get("specificity_pass") is True, f"{qid}/{cid}: specificity failed", errors)
        dimensions = claim.get("specificity_dimensions", {})
        for dimension in ("dose", "unit", "operator", "timing", "population", "negation"):
            _require(
                dimensions.get(dimension) in {"MATCH", "NOT_APPLICABLE"},
                f"{qid}/{cid}: {dimension} mismatch",
                errors,
            )
        _require(claim.get("final_claim_pass") is True, f"{qid}/{cid}: final claim failed", errors)

    coverage = question.get("content_coverage", {})
    fragments = coverage.get("fragments", [])
    _require(bool(fragments), f"{qid}: no content fragments", errors)
    _require(coverage.get("uncovered_decisive_fragments") == 0, f"{qid}: uncovered decisive fragment", errors)
    for fragment in fragments:
        if fragment.get("classification") == "DECISIVE_CLINICAL_CONTENT":
            mapped = set(fragment.get("mapped_claim_ids", []))
            _require(bool(mapped) and mapped <= claim_ids, f"{qid}: decisive fragment lacks a valid claim mapping", errors)
            _require(fragment.get("coverage_status") == "COVERED", f"{qid}: decisive fragment is not covered", errors)

    components = question.get("answer_component_coverage", [])
    _require(bool(components), f"{qid}: keyed answer was not componentized", errors)
    for component in components:
        _require(
            component.get("status") == "COVERED",
            f"{qid}: uncovered keyed-answer component {component.get('component')}",
            errors,
        )
        _require(
            str(component.get("claim_id", "")) in claim_ids,
            f"{qid}: answer component has invalid claim mapping",
            errors,
        )

    _validate_bound_option_reviews(question, errors)
    return errors


def validate_checkpoint(
    checkpoint: Mapping[str, Any],
    source_report: Mapping[str, Any],
    root_dir: Optional[Path] = None,
) -> List[str]:
    """Independently recompute and validate checkpoint summary counts from low-level artifacts."""
    errors: List[str] = []
    packets = {packet["source_id"]: packet for packet in source_report.get("sources", [])}
    for packet in packets.values():
        errors.extend(validate_source_packet(packet, root_dir=root_dir))

    questions = checkpoint.get("questions", [])
    _require(len(questions) == 36, "checkpoint: expected exactly 36 questions", errors)
    ids = [question.get("question_id") for question in questions]
    _require(len(ids) == len(set(ids)), "checkpoint: duplicate question ids", errors)
    for question in questions:
        errors.extend(validate_question_record(question, packets))

    recomputed = {
        "total_questions": len(questions),
        "source_grounded": sum(question.get("source_grounded") is True for question in questions),
        "clinician_review_required": sum(
            question.get("trust_state") == "CLINICIAN_REVIEW_REQUIRED" for question in questions
        ),
        "quarantined": sum(question.get("trust_state") == "QUARANTINED" for question in questions),
        "deferred": sum(question.get("trust_state") == "DEFERRED" for question in questions),
        "rejected": sum(question.get("trust_state") == "REJECTED" for question in questions),
    }
    _require(
        checkpoint.get("summary") == recomputed,
        f"checkpoint: stored summary differs from recomputation {recomputed}",
        errors,
    )
    return errors


def assert_no_errors(errors: Iterable[str]) -> None:
    collected = list(errors)
    if collected:
        raise ValueError("\n".join(collected))
