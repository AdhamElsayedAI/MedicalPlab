import json
from pathlib import Path

rep = json.loads(Path('reports/renal_v5/renal_v5_b500_clean_train_ceiling_report.json').read_text(encoding='utf-8'))
core = json.loads(Path('evaluation/renal/v5/renal-rerank-train-core-v5-clean-v1.json').read_text(encoding='utf-8'))
val = json.loads(Path('evaluation/renal/v5/renal-rerank-train-val-v5-clean-v1.json').read_text(encoding='utf-8'))

all_items = {it['query_id']: it for it in (core + val)}

print("=== CORE MISSES (Rank > 500) ===")
for rec in rep['train_core_clean']['per_query_records']:
    if not rec['in_b500']:
        qid = rec['query_id']
        it = all_items[qid]
        print(f"[{qid} | Rank: {rec['best_dense_rank']} | Doc Rank: {rec['gold_doc_rank']}]")
        print(f"  Q: {it['query']}")
        print(f"  P: {it['evidence_span_text'][:120]}...")

print("\n=== VAL MISSES (Rank > 500) ===")
for rec in rep['train_val_clean']['per_query_records']:
    if not rec['in_b500']:
        qid = rec['query_id']
        it = all_items[qid]
        print(f"[{qid} | Rank: {rec['best_dense_rank']} | Doc Rank: {rec['gold_doc_rank']}]")
        print(f"  Q: {it['query']}")
        print(f"  P: {it['evidence_span_text'][:120]}...")
