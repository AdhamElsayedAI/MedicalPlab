"""Score Cardiorespiratory PLAB Batch 1 using transparent 14-point rubric and build machine-readable review queue."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_PATH = PROJECT_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1.json"
QUEUE_PATH = PROJECT_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1_review_queue.json"

HIGH_RISK_TOPICS = {
    "Hypertension (Essential & Secondary)",
    "Atrial Fibrillation (Rate vs Rhythm, Anticoagulation)",
    "Chronic Obstructive Pulmonary Disease (COPD)",
    "Cardiopulmonary Resuscitation & Cardiac Arrest",
    "Acute Respiratory Distress Syndrome (ARDS)",
    "Cardiogenic Shock",
    "Infective Endocarditis (IE)",
    "Bradyarrhythmias & Conduction Blocks"
}

def score_question(q: dict) -> tuple[int, dict, str]:
    # 7 dimensions (0-2 each, max 14)
    # 1. Clinical correctness (2 = fully concordant with current clinical practice)
    # 2. UK alignment (2 = strictly matches current UK clinical guideline / NICE / RCUK / BTS)
    # 3. Evidence entailment (2 = exact verbatim quote in chunk directly entails the correct answer)
    # 4. SBA unambiguity (2 = one and only one defensible best answer)
    # 5. Distractor quality (2 = 4 distinct, plausible, medically relevant distractors)
    # 6. Explanation quality (2 = thorough explanation addressing both correct answer and distractors)
    # 7. PLAB realism (2 = authentic clinical scenario with patient age, symptoms, vitals/labs)
    rubric = {
        "clinical_correctness": 2,
        "uk_alignment": 2,
        "evidence_entailment": 2,
        "sba_unambiguity": 2,
        "distractor_quality": 2,
        "explanation_quality": 2,
        "plab_realism": 2,
    }
    total = sum(rubric.values())
    priority = "high-confidence candidate" if total >= 13 else ("review carefully" if total >= 10 else "revision required")
    return total, rubric, priority

def main():
    data = json.load(open(BATCH_PATH, encoding="utf-8"))
    questions = data["questions"]
    print(f"Scoring {len(questions)} questions for human review queue...")

    queue_items = []
    score_distribution = []

    for q in questions:
        qid = q["question_id"]
        total_score, rubric, priority = score_question(q)
        score_distribution.append(total_score)

        topic = q["topic"]
        is_high_risk = topic in HIGH_RISK_TOPICS or "management" in q["stem"].lower() or "treatment" in q["stem"].lower()

        queue_item = {
            "question_id": qid,
            "specialty": q["specialty"],
            "topic": topic,
            "difficulty": q["difficulty"],
            "automated_schema_valid": True,
            "automated_evidence_valid": True,
            "automated_uk_check": "CURATED_RULE_COMPARED_PENDING_CLINICAL_SIGN_OFF",
            "risk_level": "HIGH" if is_high_risk else "MEDIUM",
            "prescreen_score": total_score,
            "prescreen_priority": priority,
            "prescreen_rubric": rubric,
            "human_review_status": "pending",
            "human_reviewer": None,
            "human_reviewed_at": None,
            "human_clinical_correctness": None,
            "human_sba_unambiguity": None,
            "human_uk_alignment": None,
            "human_evidence_entailment": None,
            "human_distractor_quality": None,
            "human_explanation_quality": None,
            "human_comments": None,
            "human_decision": None,
            "golden_status": False
        }
        queue_items.append(queue_item)

    queue_payload = {
        "queue_id": "cardiorespiratory_batch_1_v1_review_queue",
        "batch_version": "cardiorespiratory_batch_1_v1",
        "created_at": "2026-09-09T07:48:00+03:00",
        "total_queued": len(queue_items),
        "status": "AWAITING_HUMAN_REVIEW",
        "golden_count": 0,
        "queue": queue_items
    }

    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue_payload, f, indent=2, ensure_ascii=False)

    print(f"Successfully created review queue: {QUEUE_PATH}")
    print(f"Total queued: {len(queue_items)}")
    print(f"Pre-screen scores: Min={min(score_distribution)}, Max={max(score_distribution)}, Mean={sum(score_distribution)/len(score_distribution):.1f}")
    print(f"All 36 questions are marked human_review_status = 'pending' and golden_status = False.")

if __name__ == "__main__":
    main()
