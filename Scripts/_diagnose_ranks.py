import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SCRIPTS = _ROOT / "Scripts"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import json
import numpy as np

# Load the generated items and inspect rank distribution
from curate_high_coverage_benchmark import all_items, core_ranks, val_ranks, all_chunks

print("=== BOTTOM 10 CORE RANKS (WORST) ===")
core_pairs = sorted(zip(core_ranks, all_items[:60]), key=lambda x: x[0], reverse=True)
for rank, it in core_pairs[:10]:
    cid = it["gold_chunk_ids"][0]
    ch = all_chunks[cid]
    print(f"Rank {rank:4d} | {it['query_id']} | {cid} | Doc: {it['source_document_id']}")
    print(f"  Query: {it['query']}")
    print(f"  Text snippet: {ch['text'][:180].replace(chr(10), ' ')}")
    print("-" * 60)

print("\n=== TOP 10 CORE RANKS (BEST) ===")
for rank, it in sorted(core_pairs, key=lambda x: x[0])[:10]:
    cid = it["gold_chunk_ids"][0]
    print(f"Rank {rank:4d} | {it['query_id']} | {cid} | Query: {it['query']}")
