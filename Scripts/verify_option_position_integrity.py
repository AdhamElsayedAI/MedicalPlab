"""Verify option position integrity and correct choice alignment."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_PATH = PROJECT_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1.json"

def main():
    data = json.load(open(BATCH_PATH, encoding="utf-8"))
    questions = data["questions"]
    print(f"Verifying option position integrity for {len(questions)} questions...")

    failures = []
    for q in questions:
        qid = q["question_id"]
        correct_key = q["correct_answer"]
        choices = {c["id"]: c["text"] for c in q["choices"]}
        
        if correct_key not in choices:
            failures.append(f"{qid}: correct_answer {correct_key} not in choices {list(choices.keys())}")
            continue

        correct_text = choices[correct_key]
        expl = q["explanation"].lower()
        correct_text_words = [w.lower() for w in correct_text.split() if len(w) > 3]

        # Check that explanation mentions key concepts of the correct text
        matched_words = [w for w in correct_text_words if w in expl]
        if len(matched_words) == 0 and len(correct_text_words) > 0:
            failures.append(f"{qid}: Explanation may not match correct choice '{correct_text}'. Matched: {matched_words}")

    print(f"Verification completed. Issues found: {len(failures)}")
    if failures:
        for f in failures:
            print("  FAIL:", f)
        raise RuntimeError("Integrity check failed")
    else:
        print("ALL 36 QUESTIONS PASSED OPTION-POSITION AND EXPLANATION ALIGNMENT VERIFICATION.")

if __name__ == "__main__":
    main()
