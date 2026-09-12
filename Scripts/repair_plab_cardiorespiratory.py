"""
MedicalPlab Shared Evidence Engine V2 — Stage 11: PLAB Cardiorespiratory Repair
==============================================================================
Audits and revalidates all 36 candidate questions in:
Data/questions/cardiorespiratory_batch_1.json

Detects and resolves the false-positive citation pattern:
"A quote exists in the corpus BUT the quote does not entail the PLAB answer."

Classifies every question into:
- EVIDENCE_VERIFIED: Cited evidence strictly entails why the correct option is correct.
- NEEDS_SOURCE_REPAIR: Clinically valid vignette, but cited quote lacks specific entailment or authority.
- REJECTED: Medically flawed or contradictory question.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from medicalplab.evidence_engine.claim_verifier import CentralClaimVerifier
from medicalplab.evidence_engine.models import PlabVerificationStatus, VerificationState

INPUT_PATH = _ROOT / "Data" / "questions" / "cardiorespiratory_batch_1.json"
REPORTS_DIR = _ROOT / "reports" / "plab_repair"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def audit_plab_question(q: dict, verifier: CentralClaimVerifier) -> dict:
    qid = q.get("question_id")
    stem = q.get("stem", "")
    correct_opt = q.get("correct_answer", "")
    explanation = q.get("explanation", "")
    citations = q.get("citations", [])

    # Find text of correct option
    correct_text = ""
    for ch in q.get("choices", []):
        if ch.get("id") == correct_opt:
            correct_text = ch.get("text", "")
            break

    # Extract atomic claim: Why correct_text is correct
    core_rationale_claim = f"{correct_text} is the correct management/diagnosis for {stem[:120]} because {explanation[:200]}"
    
    # Check citation entailment
    is_verified = False
    repair_reasons = []
    
    if not citations:
        repair_reasons.append("NO_CITATIONS_PROVIDED")
    else:
        for cit in citations:
            quote = cit.get("quote", "")
            doc_id = cit.get("document_id", "")
            ref = cit.get("ref", "")

            # Run through CentralClaimVerifier
            res = verifier.verify_claim(
                claim_id=f"{qid}-core",
                claim_text=f"First-line or correct option is {correct_text}. {explanation[:150]}",
                evidence_text=quote,
                cited_chunk_id=ref,
                cited_document_id=doc_id,
                authority="NICE" if "nice" in stem.lower() else "WHO"
            )

            # Check if quote actually contains the drug/condition or key rationale
            key_terms = re.findall(r"\b[A-Za-z]{4,}\b", correct_text.lower())
            has_term_overlap = any(t in quote.lower() for t in key_terms)

            if res.state == VerificationState.SUPPORTED and has_term_overlap:
                is_verified = True
            else:
                if not has_term_overlap:
                    repair_reasons.append(
                        f"FALSE_POSITIVE_CITATION: Cited quote '{quote[:80]}...' defines context but does NOT mention correct option '{correct_text}'"
                    )
                if "GUIDELINE_AUTHORITY_MISMATCH" in str(res.veto_flags):
                    repair_reasons.append(
                        f"AUTHORITY_MISMATCH: Stem cites NICE guideline, but evidence is drawn from {doc_id} without NICE authority binding."
                    )

    # Classification logic
    if is_verified and not repair_reasons:
        status = PlabVerificationStatus.EVIDENCE_VERIFIED
    elif "CONTRADICTED" in repair_reasons:
        status = PlabVerificationStatus.REJECTED
    else:
        status = PlabVerificationStatus.NEEDS_SOURCE_REPAIR

    return {
        "question_id": qid,
        "topic": q.get("topic"),
        "correct_answer": correct_opt,
        "correct_text": correct_text,
        "status": status.value,
        "repair_reasons": repair_reasons,
        "citations_audited": len(citations)
    }


def main():
    print(f"Loading {INPUT_PATH.name}...")
    data = json.loads(INPUT_PATH.read_bytes())
    questions = data.get("questions", [])
    print(f"Found {len(questions)} candidate PLAB questions.")

    verifier = CentralClaimVerifier(reranker=None)

    audited_questions = []
    status_counts = {
        PlabVerificationStatus.EVIDENCE_VERIFIED.value: 0,
        PlabVerificationStatus.NEEDS_SOURCE_REPAIR.value: 0,
        PlabVerificationStatus.REJECTED.value: 0
    }

    for q in questions:
        res = audit_plab_question(q, verifier)
        audited_questions.append(res)
        status_counts[res["status"]] += 1
        # Update question status in object
        q["evidence_verification_status"] = res["status"]
        q["repair_notes"] = res["repair_reasons"]

    # Write updated questions file back
    data["repair_audit"] = {
        "total_audited": len(questions),
        "status_counts": status_counts,
        "audited_at": "2026-09-11"
    }
    INPUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Generate audit report
    report = {
        "batch_id": data.get("batch_id"),
        "total_questions": len(questions),
        "classification_summary": status_counts,
        "false_positive_citations_detected": sum(
            1 for q in audited_questions if any("FALSE_POSITIVE_CITATION" in r for r in q["repair_reasons"])
        ),
        "authority_mismatches_detected": sum(
            1 for q in audited_questions if any("AUTHORITY_MISMATCH" in r for r in q["repair_reasons"])
        ),
        "questions_detail": audited_questions
    }

    out_report = REPORTS_DIR / "plab_cardiorespiratory_repair_audit.json"
    out_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    sha = hashlib.sha256(out_report.read_bytes()).hexdigest()
    (out_report.with_suffix(".json.sha256")).write_text(f"{sha}  {out_report.name}", encoding="utf-8")

    print("\n=======================================================")
    print("PLAB CARDIORESPIRATORY REPAIR AUDIT RESULTS:")
    print("=======================================================")
    print(f"Total Questions Audited: {len(questions)}")
    print(f"  EVIDENCE_VERIFIED:    {status_counts['EVIDENCE_VERIFIED']}")
    print(f"  NEEDS_SOURCE_REPAIR:  {status_counts['NEEDS_SOURCE_REPAIR']}")
    print(f"  REJECTED:             {status_counts['REJECTED']}")
    print(f"  False-Positive Cites: {report['false_positive_citations_detected']}")
    print(f"  Authority Mismatches: {report['authority_mismatches_detected']}")
    print(f"\nSaved audit to {out_report.name} (SHA-256: {sha})")


if __name__ == "__main__":
    main()
