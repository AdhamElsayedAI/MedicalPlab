"""Inspect top retrieved text for the 33 DEV ablation failures."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
dev = json.loads((ROOT / "evaluation/renal/renal-dev-v2.json").read_text(encoding="utf-8"))
queries = {q["query_id"]: q for q in dev["queries"]}
abl = json.loads((ROOT / "reports/renal_v2_ablation.json").read_text(encoding="utf-8"))
failures = abl.get("final_failures", [])

B_dir = ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
chunks = {}
for f in B_dir.glob("*.chunks.json"):
    for ch in json.loads(f.read_text(encoding="utf-8"))["chunks"]:
        chunks[ch["chunk_id"]] = ch

print(f"Total failures to inspect: {len(failures)}")
print("=" * 80)
for i, f in enumerate(failures, 1):
    qid = f["query_id"]
    q = queries.get(qid, {})
    top1 = f["top_10"][0] if f["top_10"] else {}
    cid = top1.get("chunk_id")
    ch = chunks.get(cid, {})
    txt = ch.get("text", "")[:200].replace("\n", " ")
    qtext = q.get("query", "")
    gold_p = q.get("gold_parent_section_ids")
    ret_p = top1.get("parent_section_id")
    sec = top1.get("section_path")
    print(f"[{i:02d}] {qid}: {qtext}")
    print(f"     Gold parent: {gold_p}")
    print(f"     Top1 retrieved: {cid} ({ret_p}) sec={sec}")
    print(f"     Top1 text: {txt}...")
    print()
