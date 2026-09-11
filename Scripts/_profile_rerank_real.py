import os
import sys
import time
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import torch
import numpy as np
from sentence_transformers import CrossEncoder

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DEV_A_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"

dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))
chunks = []
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    chunks.extend(payload.get("chunks", []))

print(f"Loaded {len(dev_a)} DEV-A queries and {len(chunks)} chunks.")

dev = torch.device("cuda:0")
reranker = CrossEncoder("Qwen/Qwen3-Reranker-0.6B", device="cuda:0", trust_remote_code=True)

# Test first DEV-A query with first 20, 30, 50 real chunks
q_text = dev_a[0]["query"]
pairs_20 = [[q_text, chunks[i]["text"]] for i in range(20)]
pairs_30 = [[q_text, chunks[i]["text"]] for i in range(30)]
pairs_50 = [[q_text, chunks[i]["text"]] for i in range(50)]

print("\nTesting real corpus pairs with torch.cuda.synchronize():")

for k, pairs in [(20, pairs_20), (30, pairs_30), (50, pairs_50)]:
    torch.cuda.reset_peak_memory_stats(dev)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    _ = reranker.predict(pairs, batch_size=k, show_progress_bar=False)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - t0
    peak_alloc = torch.cuda.max_memory_allocated(dev) / (1024**2)
    peak_res = torch.cuda.max_memory_reserved(dev) / (1024**2)
    print(f"Depth K={k}: Elapsed = {elapsed*1000:.1f} ms | Peak Alloc = {peak_alloc:.1f} MB | Peak Res = {peak_res:.1f} MB")

# Now test what happens if we do a small loop of 5 queries at K=30 and K=50
print("\nTesting loop of 5 DEV-A queries:")
for k in [20, 30, 50]:
    times = []
    torch.cuda.reset_peak_memory_stats(dev)
    for q_idx in range(5):
        q = dev_a[q_idx]["query"]
        p_list = [[q, chunks[i]["text"]] for i in range(k)]
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        _ = reranker.predict(p_list, batch_size=k, show_progress_bar=False)
        torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
    print(f"K={k} (5 queries): Mean = {np.mean(times)*1000:.1f} ms, Max = {np.max(times)*1000:.1f} ms | Peak Alloc = {torch.cuda.max_memory_allocated(dev)/(1024**2):.1f} MB")
