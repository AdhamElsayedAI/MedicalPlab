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

QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "

def encode_queries(q_list):
    texts = [QUERY_INSTRUCTION + q for q in q_list]
    with torch.inference_mode():
        encoded = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        out = model(**encoded)
        mask = encoded["attention_mask"].unsqueeze(-1)
        embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return torch.nn.functional.normalize(embs, p=2, dim=1).cpu().numpy().astype(np.float32)

t_embs = encode_queries([it["query"] for it in train_80])
da_embs = encode_queries([it["query"] for it in dev_a])
db_embs = encode_queries([it["query"] for it in dev_b])

sims_a = t_embs @ da_embs.T
sims_b = t_embs @ db_embs.T

print("Top similarities against DEV-A >= 0.88:")
for ti in range(80):
    for ai in range(len(dev_a)):
        if sims_a[ti, ai] >= 0.88:
            print(f"TRAIN[{ti}] ({train_80[ti]['query_id']}): '{train_80[ti]['query']}'")
            print(f"  vs DEV-A[{ai}] ({dev_a[ai]['query_id']}): '{dev_a[ai]['query']}'")
            print(f"  Similarity = {sims_a[ti, ai]:.4f}\n")

print("\nTop similarities against DEV-B >= 0.88:")
for ti in range(80):
    for bi in range(len(dev_b)):
        if sims_b[ti, bi] >= 0.88:
            print(f"TRAIN[{ti}] ({train_80[ti]['query_id']}): '{train_80[ti]['query']}'")
            print(f"  vs DEV-B[{bi}] ({dev_b[bi]['query_id']}): '{dev_b[bi]['query']}'")
            print(f"  Similarity = {sims_b[ti, bi]:.4f}\n")
