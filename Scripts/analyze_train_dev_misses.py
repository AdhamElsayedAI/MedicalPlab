import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / ".renal_env"))
sys.path.insert(0, str(root / "src"))

from medicalplab.learn.renal_v7_retriever import RenalV7MultiChannelRetriever

train_dev = json.loads((root / "evaluation/renal/v7/renal-train-dev-v7.json").read_bytes())
retriever = RenalV7MultiChannelRetriever(root / "Data")
retriever.load()

misses = []
for idx, item in enumerate(train_dev):
    q = item["query"]
    gold = set(item["gold_chunk_ids"])
    results = retriever.retrieve(q, top_k=10)
    top1 = results[0].chunk_id
    gold_ranks = [r_i + 1 for r_i, r in enumerate(results) if r.chunk_id in gold]
    
    if top1 not in gold:
        misses.append({
            "idx": idx,
            "query": q,
            "target_topic": item.get("target_topic"),
            "evidence_quote": item.get("evidence_quote"),
            "gold_chunk_ids": list(gold),
            "top1_chunk_id": top1,
            "top1_title": results[0].chunk.get("doc_title"),
            "top1_section": results[0].chunk.get("section_path"),
            "top1_heading": results[0].chunk.get("heading"),
            "top1_score": results[0].rerank_score,
            "gold_ranks": gold_ranks,
            "gold_top_rank": gold_ranks[0] if gold_ranks else None
        })

print(f"Total misses at rank 1: {len(misses)} / {len(train_dev)}")
gold_in_top5 = sum(1 for m in misses if m["gold_top_rank"] and m["gold_top_rank"] <= 5)
print(f"Of the {len(misses)} misses, {gold_in_top5} have gold chunk in ranks 2-5.")

print("\n--- SAMPLE MISSES ---")
for m in misses[:10]:
    print(f"\nQuery {m['idx']}: {m['query']}")
    print(f"  Target topic: {m['target_topic']}")
    print(f"  Evidence quote: {m['evidence_quote']}")
    print(f"  Gold chunks: {m['gold_chunk_ids']} -> Ranked at: {m['gold_ranks']}")
    print(f"  Top-1 returned: {m['top1_chunk_id']} ({m['top1_title']} > {m['top1_section']} > {m['top1_heading']})")
