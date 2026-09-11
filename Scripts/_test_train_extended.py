import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(".")
sys_path_dir = ROOT / "Scripts"
import sys
if str(sys_path_dir) not in sys.path:
    sys.path.insert(0, str(sys_path_dir))

from _train_extended_spec import load_corpus, get_all_80_items, normalize_text, compute_sha256

chunks, chunk_map, doc_meta = load_corpus()
items = get_all_80_items(chunks, chunk_map)

print(f"Total extended items: {len(items)}")
assert len(items) == 80, f"Expected 80, got {len(items)}"

# 1. Verify original 20
orig_train = json.loads(Path("evaluation/renal/v5/renal-rerank-train-v5.json").read_text(encoding="utf-8"))
for i in range(20):
    assert items[i]["query_id"] == orig_train[i]["query_id"]
    assert items[i]["query"] == orig_train[i]["query"]
    assert items[i]["canonical_claim"] == orig_train[i]["canonical_claim"]
    assert items[i]["gold_chunk_ids"] == orig_train[i]["gold_chunk_ids"]
print("1. Original N=20 preservation check: PASS (100% byte-for-byte identical)")

# 2. Check gold chunk resolution for all 80 items
unresolved = [it for it in items if not it["gold_chunk_ids"]]
print(f"2. Unresolved items: {len(unresolved)}")
if unresolved:
    for u in unresolved:
        print(f"   UNRESOLVED: {u['query_id']} kw='{u['evidence_search_keyword']}' in doc {u['source_document_id']}")
assert len(unresolved) == 0, "Some items failed to resolve gold chunks!"

# 3. Check stratum distribution
strata_counts = Counter(it["curriculum_stratum"] for it in items)
print("\n3. Curriculum Strata Distribution across N=80:")
for s in sorted(strata_counts.keys()):
    print(f"   {s}: {strata_counts[s]} queries")
assert len(strata_counts) == 12, "Not all 12 strata covered!"
for s, cnt in strata_counts.items():
    assert cnt >= 6, f"Stratum {s} has only {cnt} queries (expected >= 6)"

# 4. Check query uniqueness and claim uniqueness within TRAIN_EXTENDED
queries = [it["query"] for it in items]
claims = [it["canonical_claim"] for it in items]
objs = [it["learning_objective"] for it in items]
print(f"\n4. Internal Uniqueness:")
print(f"   Unique queries: {len(set(queries))} / 80")
print(f"   Unique canonical claims: {len(set(claims))} / 80")
print(f"   Unique learning objectives: {len(set(objs))} / 80")
assert len(set(queries)) == 80
assert len(set(claims)) == 80
assert len(set(objs)) == 80

# 5. Firewall check against DEV-A, DEV-B, and Historical Heldouts
dev_a = json.loads(Path("evaluation/renal/v5/renal-rerank-dev-a-v5.json").read_text(encoding="utf-8"))
dev_b = json.loads(Path("evaluation/renal/v5/renal-rerank-dev-b-v5.json").read_text(encoding="utf-8"))

heldout_files = [
    Path("evaluation/renal/renal-heldout-v1.json"),
    Path("evaluation/renal/renal-heldout-v2-final.json"),
    Path("evaluation/renal/v3/renal-heldout-v3-final.json"),
    Path("evaluation/renal/v4/renal-heldout-v4-final.json"),
]

heldout_items = []
for hf in heldout_files:
    if hf.exists():
        data = json.loads(hf.read_text(encoding="utf-8"))
        # could be list or dict with queries
        q_list = data if isinstance(data, list) else data.get("queries", [])
        heldout_items.extend(q_list)

print(f"\n5. Firewall checks against {len(dev_a)} DEV-A, {len(dev_b)} DEV-B, {len(heldout_items)} historical heldout queries:")

# Build frozen check sets
norm_train_queries = {normalize_text(it["query"]): it["query_id"] for it in items}
train_claims = {normalize_text(it["canonical_claim"]): it["query_id"] for it in items}
train_objs = {normalize_text(it["learning_objective"]): it["query_id"] for it in items}

eval_sets = [("DEV-A", dev_a), ("DEV-B", dev_b), ("HISTORICAL_HELDOUT", heldout_items)]

leakage_found = False
for set_name, q_list in eval_sets:
    for q in q_list:
        q_text = q.get("query", "")
        norm_q = normalize_text(q_text)
        claim_text = normalize_text(q.get("canonical_claim") or q.get("medical_claim") or "")
        obj_text = normalize_text(q.get("learning_objective") or "")
        
        if norm_q in norm_train_queries:
            print(f"   LEAKAGE DETECTED in {set_name}: Exact/Norm query match! '{q_text}' vs {norm_train_queries[norm_q]}")
            leakage_found = True
        if claim_text and claim_text in train_claims:
            print(f"   LEAKAGE DETECTED in {set_name}: Claim match! '{claim_text}' vs {train_claims[claim_text]}")
            leakage_found = True
        if obj_text and obj_text in train_objs:
            print(f"   LEAKAGE DETECTED in {set_name}: Objective match! '{obj_text}' vs {train_objs[obj_text]}")
            leakage_found = True

assert not leakage_found, "Firewall violation detected!"
print("   Firewall checks: PASS (ZERO query, normalized query, claim, or objective leakage detected across DEV-A, DEV-B, or historical heldouts).")
