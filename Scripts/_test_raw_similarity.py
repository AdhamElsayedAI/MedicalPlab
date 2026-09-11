import json
from pathlib import Path
import numpy as np

ROOT = Path(".")
sys_path_dir = ROOT / "Scripts"
import sys
if str(sys_path_dir) not in sys.path:
    sys.path.insert(0, str(sys_path_dir))

from _train_extended_spec import load_corpus, get_all_80_items
import torch
from transformers import AutoModel, AutoTokenizer

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
chunks, chunk_map, doc_meta = load_corpus()
train_80 = get_all_80_items(chunks, chunk_map)

dev_a = json.loads(Path("evaluation/renal/v5/renal-rerank-dev-a-v5.json").read_text(encoding="utf-8"))
dev_b = json.loads(Path("evaluation/renal/v5/renal-rerank-dev-b-v5.json").read_text(encoding="utf-8"))

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
model = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

def encode_raw_queries(q_list):
    # Encode pure query string without instruction
    with torch.inference_mode():
        encoded = tokenizer(q_list, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        out = model(**encoded)
        mask = encoded["attention_mask"].unsqueeze(-1)
        embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return torch.nn.functional.normalize(embs, p=2, dim=1).cpu().numpy().astype(np.float32)

t_embs = encode_raw_queries([it["query"] for it in train_80])
da_embs = encode_raw_queries([it["query"] for it in dev_a])
db_embs = encode_raw_queries([it["query"] for it in dev_b])

sims_a = t_embs @ da_embs.T
sims_b = t_embs @ db_embs.T

print(f"Raw query encoding:")
print(f"Max cosine vs DEV-A: {np.max(sims_a):.4f}")
print(f"Max cosine vs DEV-B: {np.max(sims_b):.4f}")

# Check if any pair has >= 0.92
high_a = [(i, j, sims_a[i, j]) for i in range(80) for j in range(len(dev_a)) if sims_a[i, j] >= 0.92]
high_b = [(i, j, sims_b[i, j]) for i in range(80) for j in range(len(dev_b)) if sims_b[i, j] >= 0.92]
print(f"Pairs >= 0.92 vs DEV-A: {len(high_a)}")
for ti, ai, sim in high_a:
    print(f"  T{train_80[ti]['query_id']}: '{train_80[ti]['query']}' vs DA: '{dev_a[ai]['query']}' ({sim:.4f})")

print(f"Pairs >= 0.92 vs DEV-B: {len(high_b)}")
for ti, bi, sim in high_b:
    print(f"  T{train_80[ti]['query_id']}: '{train_80[ti]['query']}' vs DB: '{dev_b[bi]['query']}' ({sim:.4f})")
