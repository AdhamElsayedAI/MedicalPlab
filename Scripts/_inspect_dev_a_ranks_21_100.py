import json
from pathlib import Path

ROOT = Path(".")
diag = json.loads((ROOT / "reports" / "renal_v5" / "renal_v5_first_stage_diagnostic.json").read_bytes())
queries_21_100 = [q for q in diag["detailed_results"] if q["best_passage_first_stage_rank"] is not None and 21 <= q["best_passage_first_stage_rank"] <= 100]

print(f"Total DEV-A queries with gold passage rank 21-100: {len(queries_21_100)}")
for q in queries_21_100:
    print("=" * 70)
    print(f"Query ID: {q['query_id']} | Stratum: {q['curriculum_stratum']}")
    print(f"Query: {q['query']}")
    print(f"Gold Doc: {q['gold_doc_id']} (Rank: {q['gold_doc_rank']})")
    print(f"Best Passage Rank: {q['best_passage_first_stage_rank']}")
    print(f"Category: {q['diagnosis_category']}")
