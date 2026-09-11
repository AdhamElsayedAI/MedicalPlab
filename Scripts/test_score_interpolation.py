import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / ".renal_env"))
sys.path.insert(0, str(root / "src"))

import numpy as np
from medicalplab.learn.renal_v7_retriever import RenalV7MultiChannelRetriever, MEDICAL_RERANKER_INSTRUCTION

train_dev = json.loads((root / "evaluation/renal/v7/renal-train-dev-v7.json").read_bytes())
retriever = RenalV7MultiChannelRetriever(root / "Data")
retriever.load()

query_cand_data = []
for item in train_dev:
    q = item["query"]
    gold = set(item["gold_chunk_ids"])
    cands = retriever.acquire_candidates(q, top_k=50)
    instruction_query = MEDICAL_RERANKER_INSTRUCTION + q
    pairs = [[instruction_query, retriever._rendered_passages[retriever._chunk_id_to_idx[c.chunk_id]]] for c in cands]
    scores = retriever._reranker.predict(pairs, batch_size=16, show_progress_bar=False)
    scores = np.asarray(scores, dtype=np.float32).reshape(-1)
    for i, c in enumerate(cands):
        c.rerank_score = float(scores[i])
    query_cand_data.append((gold, cands))

print("\n--- Testing Score Interpolation on TRAIN_DEV ---")
for beta in [0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 50.0, 100.0]:
    h1 = 0
    h5 = 0
    for gold, cands in query_cand_data:
        ranked = sorted(cands, key=lambda c: c.rerank_score + beta * c.fused_score, reverse=True)
        if ranked[0].chunk_id in gold:
            h1 += 1
        if any(c.chunk_id in gold for c in ranked[:5]):
            h5 += 1
    print(f"Beta {beta:5.1f} -> Hit@1: {h1}/80 ({h1/80*100:.2f}%), Hit@5: {h5}/80 ({h5/80*100:.2f}%)")
