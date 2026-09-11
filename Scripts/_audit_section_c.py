import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import torch

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import CrossEncoder

print("=" * 70)
print("SECTION C AUDIT: LATENCY / DEVICE / MEMORY ARCHITECTURE")
print("=" * 70)

# 1. Device properties
assert torch.cuda.is_available(), "CUDA unavailable!"
dev = torch.device("cuda:0")
props = torch.cuda.get_device_properties(0)
total_vram_bytes = props.total_memory
total_vram_mb = total_vram_bytes / (1024**2)
total_vram_gb = total_vram_bytes / (1024**3)

print(f"Device Name: {props.name}")
print(f"Compute Capability: {props.major}.{props.minor}")
print(f"Physical Dedicated VRAM: {total_vram_bytes:,} bytes ({total_vram_mb:.1f} MB / {total_vram_gb:.2f} GB)")

# 2. Load reranker and check model internals
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
reranker = CrossEncoder(RERANK_MODEL_ID, device="cuda:0", trust_remote_code=True)
model = reranker.model

print(f"\nReranker Model Class: {type(model).__name__}")
print(f"Model Device: {model.device}")
print(f"Model Dtype: {model.dtype}")
print(f"HF device_map: {getattr(model, 'hf_device_map', None)}")
print(f"Is model offloaded? {hasattr(model, '_hf_hook') or hasattr(model, 'hf_device_map')}")

# Initial memory
allocated_mb = torch.cuda.memory_allocated(dev) / (1024**2)
reserved_mb = torch.cuda.memory_reserved(dev) / (1024**2)
print(f"Model Loaded VRAM: Allocated = {allocated_mb:.1f} MB, Reserved = {reserved_mb:.1f} MB")

# 3. Test timing with warmup and synchronize
# Let's test a dummy query with 20 pairs, batch_size=20 vs batch_size=16
dummy_query = "What is the role of tubuloglomerular feedback in maintaining GFR stability?"
dummy_passage = "Tubuloglomerular feedback is an intrinsic mechanism of the kidney where macula densa cells sense luminal sodium chloride delivery and adjust glomerular filtration rate by constricting the afferent arteriole."
pairs_20 = [[dummy_query, dummy_passage] for _ in range(20)]

# Warmup
torch.cuda.synchronize()
_ = reranker.predict(pairs_20[:2], batch_size=2, show_progress_bar=False)
torch.cuda.synchronize()

# Time K=20 with synchronize
import time
torch.cuda.reset_peak_memory_stats(dev)
torch.cuda.synchronize()
t0 = time.perf_counter()
_ = reranker.predict(pairs_20, batch_size=20, show_progress_bar=False)
torch.cuda.synchronize()
t_k20 = time.perf_counter() - t0
peak_k20_mb = torch.cuda.max_memory_allocated(dev) / (1024**2)
res_k20_mb = torch.cuda.max_memory_reserved(dev) / (1024**2)

print(f"\nTiming K=20 (batch_size=20):")
print(f"  Elapsed: {t_k20*1000:.1f} ms")
print(f"  Peak Allocated VRAM: {peak_k20_mb:.1f} MB")
print(f"  Peak Reserved VRAM: {res_k20_mb:.1f} MB")

# Check what happens with batch_size=30
pairs_30 = [[dummy_query, dummy_passage] for _ in range(30)]
torch.cuda.reset_peak_memory_stats(dev)
torch.cuda.synchronize()
t0 = time.perf_counter()
_ = reranker.predict(pairs_30, batch_size=30, show_progress_bar=False)
torch.cuda.synchronize()
t_k30 = time.perf_counter() - t0
peak_k30_mb = torch.cuda.max_memory_allocated(dev) / (1024**2)
res_k30_mb = torch.cuda.max_memory_reserved(dev) / (1024**2)

print(f"\nTiming K=30 (batch_size=30):")
print(f"  Elapsed: {t_k30*1000:.1f} ms")
print(f"  Peak Allocated VRAM: {peak_k30_mb:.1f} MB")
print(f"  Peak Reserved VRAM: {res_k30_mb:.1f} MB")

print(f"\nPhysical VRAM limit is {total_vram_mb:.1f} MB.")
print(f"Any allocation above {total_vram_mb:.1f} MB forces Windows WDDM to spill into Windows Shared GPU Memory (PCIe paging).")
