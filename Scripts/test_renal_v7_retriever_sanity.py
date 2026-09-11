"""
Sanity check script for RenalV7MultiChannelRetriever.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / ".renal_env"))
sys.path.insert(0, str(_ROOT / "src"))

from medicalplab.learn.renal_v7_retriever import RenalV7MultiChannelRetriever

def main():
    print("Initializing RenalV7MultiChannelRetriever...")
    retriever = RenalV7MultiChannelRetriever(_ROOT / "Data", candidate_depth=50)
    retriever.load()
    print("Retriever loaded successfully.")

    test_query = "What is the primary early pathological hallmark of chronic kidney disease affecting the glomeruli?"
    print(f"Running candidate acquisition for: '{test_query}'...")
    candidates = retriever.acquire_candidates(test_query, top_k=50)
    print(f"Acquired {len(candidates)} candidates.")

    top_cand = candidates[0]
    print(f"Top-1 Candidate ID: {top_cand.chunk_id} | Document: {top_cand.document_id}")
    print(f"Fused Score: {top_cand.fused_score:.5f}")
    print(f"Channel Ranks: {top_cand.channel_ranks}")

    print("Running end-to-end retrieve (Top-5)...")
    hits = retriever.retrieve(test_query, top_k=5)
    for i, h in enumerate(hits):
        print(f"Hit @{i+1}: {h.chunk_id} | Score: {h.rerank_score:.4f} | Heading: {h.chunk.get('heading')}")

    print("Sanity check PASSED.")

if __name__ == "__main__":
    main()
