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

dev_a = json.loads(Path("evaluation/renal/v5/renal-rerank-dev-a-v5.json").read_text(encoding="utf-8"))
dev_b = json.loads(Path("evaluation/renal/v5/renal-rerank-dev-b-v5.json").read_text(encoding="utf-8"))

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
model = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

def encode_raw_queries(q_list):
    with torch.inference_mode():
        encoded = tokenizer(q_list, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        out = model(**encoded)
        mask = encoded["attention_mask"].unsqueeze(-1)
        embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return torch.nn.functional.normalize(embs, p=2, dim=1).cpu().numpy().astype(np.float32)

da_embs = encode_raw_queries([it["query"] for it in dev_a])
db_embs = encode_raw_queries([it["query"] for it in dev_b])

# Candidate replacements for 30, 36, 46, 47:
replacements = {
    # 30 (STR-02): Urate handling / URAT1 & GLUT9 in proximal tubule
    30: ("How do URAT1 and GLUT9 coordinate proximal tubular urate reabsorption?",
         "DOC-PMC-RENAL-0019", "urate", ["Proximal Tubule", "Urate"]),
    # 36 (STR-04): 1-alpha-hydroxylase regulation in renal tubular cells
    36: ("How does parathyroid hormone stimulate renal 1-alpha-hydroxylase activity to produce calcitriol?",
         "DOC-PMC-RENAL-0024", "calcitriol", ["Renal Endocrine", "Vitamin D"]),
    # 46 (STR-05): Bartter vs Gitelman syndrome electrolyte distinction
    46: ("What transport defects distinguish Bartter syndrome from Gitelman syndrome?",
         "DOC-PMC-RENAL-0020", "sodium", ["Tubulopathies"]),
    # 47 (STR-06): Beta-intercalated cell pendrin vs alpha-intercalated cell AE1 polarity
    47: ("How does pendrin coordinate with AE4 in collecting duct intercalated cells during alkalemia?",
         "DOC-PMC-RENAL-0021", "intercalated", ["Intercalated Polarity"]),
}

# Test similarities for these candidate replacement queries
new_q_texts = [r[0] for r in replacements.values()]
new_embs = encode_raw_queries(new_q_texts)

sims_a = new_embs @ da_embs.T
sims_b = new_embs @ db_embs.T

for i, (k, spec) in enumerate(replacements.items()):
    max_a = np.max(sims_a[i])
    max_b = np.max(sims_b[i])
    print(f"Replacement {k}: '{spec[0]}'")
    print(f"  Max vs DEV-A: {max_a:.4f}, Max vs DEV-B: {max_b:.4f}")
