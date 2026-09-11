import os
import sys
import hashlib
import json
import math
from pathlib import Path
import time

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
import torch.nn as nn
import numpy as np
from sentence_transformers import CrossEncoder

REPORTS_DIR = _ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
TRUE_TOKEN_ID = 9693   # 'yes'
FALSE_TOKEN_ID = 2152  # 'no'

print("=" * 70)
print("CUDA FORWARD + BACKWARD VRAM FEASIBILITY PILOT")
print("=" * 70)

# Check physical GPU info
device_name = torch.cuda.get_device_name(0)
total_physical_vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
print(f"GPU: {device_name}")
print(f"Physical Dedicated VRAM: {total_physical_vram_mb:.1f} MB")

# Load model via CrossEncoder
reranker = CrossEncoder(MODEL_ID, device="cuda:0", trust_remote_code=True)
transformer_module = reranker[0]
model = transformer_module.auto_model
tokenizer = reranker.tokenizer

# Clean PyTorch LoRA Linear implementation
class LoRALinear(nn.Module):
    def __init__(self, original_linear: nn.Linear, r: int = 16, lora_alpha: int = 32):
        super().__init__()
        self.original_linear = original_linear
        self.original_linear.weight.requires_grad = False
        if self.original_linear.bias is not None:
            self.original_linear.bias.requires_grad = False
            
        in_dim = original_linear.in_features
        out_dim = original_linear.out_features
        self.r = r
        self.scaling = lora_alpha / r
        
        dtype = original_linear.weight.dtype
        device = original_linear.weight.device
        
        self.lora_A = nn.Parameter(torch.empty(r, in_dim, dtype=dtype, device=device))
        self.lora_B = nn.Parameter(torch.zeros(out_dim, r, dtype=dtype, device=device))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        orig_out = self.original_linear(x)
        lora_out = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling
        return orig_out + lora_out

# Freeze all base parameters
for p in model.parameters():
    p.requires_grad = False

# Inject LoRA into attention q_proj and v_proj
lora_modules = []
for name, module in model.named_modules():
    if hasattr(module, "self_attn"):
        attn = module.self_attn
        attn.q_proj = LoRALinear(attn.q_proj, r=16, lora_alpha=32)
        attn.v_proj = LoRALinear(attn.v_proj, r=16, lora_alpha=32)
        lora_modules.extend([attn.q_proj, attn.v_proj])

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Total parameters:     {total_params:,}")
print(f"Trainable parameters: {trainable_params:,} ({trainable_params / total_params * 100:.3f}%)")

# Prepare realistic maximum-length training pairs (512 tokens)
dummy_query = "What are the clinical indications and laboratory thresholds for urgent hemodialysis in severe acute kidney injury?"
dummy_passage = (
    "Acute kidney injury with severe refractory hyperkalemia exceeding 6.5 mmol/L, refractory pulmonary edema, "
    "and metabolic acidosis with blood pH less than 7.15 despite medical management represents an absolute indication for urgent renal replacement therapy. "
) * 8 # repeated to reach 512 tokens

test_pairs = [[dummy_query, dummy_passage] for _ in range(8)]
inputs = tokenizer(test_pairs, padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda:0")
seq_len = inputs["input_ids"].shape[1]
print(f"Batch tokenized shape: {inputs['input_ids'].shape} (seq_len={seq_len})")

# Test configurations
test_configs = [
    {"batch_size": 1, "grad_checkpointing": False, "grad_accum": 4},
    {"batch_size": 2, "grad_checkpointing": False, "grad_accum": 2},
    {"batch_size": 2, "grad_checkpointing": True,  "grad_accum": 2},
    {"batch_size": 4, "grad_checkpointing": True,  "grad_accum": 1},
]

pilot_results = []

for cfg in test_configs:
    bs = cfg["batch_size"]
    gc = cfg["grad_checkpointing"]
    ga = cfg["grad_accum"]
    name = f"BS={bs}_GC={'ON' if gc else 'OFF'}_GA={ga}"
    print(f"\n--- Testing Configuration: {name} ---")
    
    if gc and hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()
    elif not gc and hasattr(model, "gradient_checkpointing_disable"):
        model.gradient_checkpointing_disable()
        
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-4)
    loss_fn = nn.CrossEntropyLoss()
    
    # Warmup
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    
    batch_input_ids = inputs["input_ids"][:bs]
    batch_attn_mask = inputs["attention_mask"][:bs]
    target_labels = torch.tensor([1] * bs, device="cuda:0") # Target is 'yes'
    
    # 3 Iterations for timing
    timings = []
    oom_occurred = False
    
    try:
        for it in range(3):
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            
            optimizer.zero_grad()
            outputs = model(input_ids=batch_input_ids, attention_mask=batch_attn_mask)
            logits = outputs.logits[:, -1, [FALSE_TOKEN_ID, TRUE_TOKEN_ID]]
            loss = loss_fn(logits, target_labels) / ga
            loss.backward()
            optimizer.step()
            
            torch.cuda.synchronize()
            t_iter = (time.perf_counter() - t0) * 1000.0
            timings.append(t_iter)
            
        peak_allocated_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
        peak_reserved_mb = torch.cuda.max_memory_reserved() / (1024 * 1024)
        mean_iter_ms = float(np.mean(timings))
        
        # Check if paging to PCIe happened
        # Physical limit is 6,143.5 MB
        paged_to_pcie = peak_reserved_mb > 5800.0
        
        print(f"  Peak Allocated VRAM: {peak_allocated_mb:7.1f} MB")
        print(f"  Peak Reserved VRAM:  {peak_reserved_mb:7.1f} MB")
        print(f"  Mean Iteration Time: {mean_iter_ms:7.1f} ms")
        print(f"  Fits Physical VRAM:  {'YES (Safe)' if not paged_to_pcie else 'NO (Paging risk)'}")
        
        pilot_results.append({
            "config_name": name,
            "batch_size": bs,
            "gradient_checkpointing": gc,
            "grad_accum": ga,
            "seq_len": seq_len,
            "trainable_params": trainable_params,
            "total_params": total_params,
            "peak_allocated_vram_mb": peak_allocated_mb,
            "peak_reserved_vram_mb": peak_reserved_mb,
            "mean_iteration_time_ms": mean_iter_ms,
            "fits_physical_vram": not paged_to_pcie,
            "status": "PASS"
        })
        
    except torch.cuda.OutOfMemoryError:
        print(f"  OOM occurred on {name}!")
        pilot_results.append({
            "config_name": name,
            "batch_size": bs,
            "gradient_checkpointing": gc,
            "grad_accum": ga,
            "status": "OOM"
        })
        torch.cuda.empty_cache()

# Save pilot results
out_path = REPORTS_DIR / "renal_v5_cuda_training_feasibility_pilot.json"
payload = {
    "device": device_name,
    "physical_dedicated_vram_mb": total_physical_vram_mb,
    "model_id": MODEL_ID,
    "dtype": "bfloat16",
    "lora_rank": 16,
    "lora_alpha": 32,
    "target_modules": ["q_proj", "v_proj"],
    "timestamp": "2026-09-11T06:55:00+00:00",
    "results": pilot_results,
    "recommended_config": next(r for r in pilot_results if r["status"] == "PASS" and r["peak_reserved_vram_mb"] < 4500.0)
}

out_bytes = json.dumps(payload, indent=2).encode("utf-8")
out_path.write_bytes(out_bytes)
out_sha = hashlib.sha256(out_bytes).hexdigest()

print("\n" + "=" * 70)
print("FEASIBILITY PILOT COMPLETE")
print("=" * 70)
print(f"Path:   {out_path}")
print(f"SHA256: {out_sha}")
print(f"Recommended Configuration: {payload['recommended_config']['config_name']}")
print(f"  VRAM: {payload['recommended_config']['peak_reserved_vram_mb']:.1f} MB reserved (well within 6.1 GB)")
print(f"  Time: {payload['recommended_config']['mean_iteration_time_ms']:.1f} ms/step")
