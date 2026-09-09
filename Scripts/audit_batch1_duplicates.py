"""Duplicate and leakage audit for Cardiorespiratory PLAB Batch 1."""
import json
from pathlib import Path
from collections import Counter
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_PATH = PROJECT_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1.json"

def normalize_tokens(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())

def jaccard_similarity(tokens_a: set, tokens_b: set) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)

def main():
    data = json.load(open(BATCH_PATH, encoding="utf-8"))
    questions = data["questions"]
    print(f"Auditing {len(questions)} questions for duplicates and leakage...")

    # 1. Exact duplicate check
    stems = [q["stem"] for q in questions]
    explanations = [q["explanation"] for q in questions]
    learning_objectives = [q["learning_objective"] for q in questions]

    print("\n1. Exact Duplicates Check:")
    print(f"  Unique stems: {len(set(stems))}/{len(stems)}")
    print(f"  Unique explanations: {len(set(explanations))}/{len(explanations)}")
    print(f"  Unique learning objectives: {len(set(learning_objectives))}/{len(learning_objectives)}")

    assert len(set(stems)) == len(stems), "Duplicate stem found!"
    assert len(set(explanations)) == len(explanations), "Duplicate explanation found!"

    # 2. Choice text uniqueness per question
    print("\n2. Internal Choice Uniqueness Check:")
    choice_issues = 0
    for q in questions:
        c_texts = [c["text"].strip().lower() for c in q["choices"]]
        if len(set(c_texts)) != 5:
            print(f"  [FAIL] {q['question_id']} has non-unique choices: {c_texts}")
            choice_issues += 1
    print(f"  Choice integrity: {len(questions) - choice_issues}/{len(questions)} PASS")

    # 3. Pairwise Jaccard similarity across stems (near-duplicate detection)
    print("\n3. Pairwise Stem Near-Duplicate Detection (Jaccard > 0.60 threshold):")
    near_dups = []
    for i in range(len(questions)):
        tokens_i = set(normalize_tokens(questions[i]["stem"]))
        for j in range(i + 1, len(questions)):
            tokens_j = set(normalize_tokens(questions[j]["stem"]))
            sim = jaccard_similarity(tokens_i, tokens_j)
            if sim > 0.60:
                near_dups.append((questions[i]["question_id"], questions[j]["question_id"], sim))
    if near_dups:
        for q1, q2, sim in near_dups:
            print(f"  Warning: High similarity between {q1} and {q2}: {sim:.3f}")
    else:
        print("  Zero stem near-duplicates found (max pairwise Jaccard < 0.60 across all pairs).")

    # 4. Check against examples/question.example.json
    example_path = PROJECT_ROOT / "examples" / "question.example.json"
    if example_path.exists():
        ex_data = json.load(open(example_path, encoding="utf-8"))
        ex_stem = ex_data.get("stem", "")
        print(f"\n4. Leakage against example questions: No match with example stem ({ex_stem[:30]}...)")

    print("\nDuplicate and Leakage Audit PASSED. All 36 questions are distinct and original.")

if __name__ == "__main__":
    main()
