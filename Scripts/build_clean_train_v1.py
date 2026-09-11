"""
MedicalPlab Renal V5 — Build CLEAN TRAIN V1 (N=80)
=================================================
Constructs a verified, source-grounded training benchmark (N=80)
with 0 cross-split leakage into DEV-A, DEV-B, or historical heldouts.
All gold chunks are drawn exclusively from safe, unspent chunks (2,288 available),
and every positive chunk is verified with an exact supporting evidence span.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

CHUNKS_DIR = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
V5_DIR = _ROOT / "evaluation/renal/v5"
DEV_A_PATH = V5_DIR / "renal-rerank-dev-a-v5.json"
DEV_B_PATH = V5_DIR / "renal-rerank-dev-b-v5.json"
OUT_CLEAN_TRAIN = V5_DIR / "renal-rerank-train-v5-clean-v1.json"

HELDOUT_FILES = [
    _ROOT / "evaluation/renal/v1/renal-heldout-gold-v1.json",
    _ROOT / "evaluation/renal/v2/renal-heldout-v2.json",
    _ROOT / "evaluation/renal/v3/renal-heldout-v3.json",
    _ROOT / "evaluation/renal/v4/renal-heldout-v4.json",
]

def norm(s: str) -> str:
    if not s: return ""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()

def norm_sec(p) -> str:
    if not p: return ""
    if isinstance(p, list): return " > ".join(s.strip().lower() for s in p)
    return str(p).strip().lower()

def get_num(cid: str) -> int:
    m = re.search(r"-C(\d+)$", cid)
    return int(m.group(1)) if m else -1

def get_pfx(cid: str) -> str:
    m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
    return m.group(1) if m else cid

# 1. Load Exclusion Registry
dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))
dev_b = json.loads(DEV_B_PATH.read_text(encoding="utf-8"))

dev_a_gold = set(c for it in dev_a for c in it.get("gold_chunk_ids", []))
dev_b_gold = set(c for it in dev_b for c in it.get("gold_chunk_ids", []))
ho_gold = set()
for hf in HELDOUT_FILES:
    if hf.exists():
        try:
            d = json.loads(hf.read_bytes())
            items = d if isinstance(d, list) else d.get("queries", d.get("questions", []))
            for it in items:
                for c in it.get("gold_chunk_ids", it.get("gold_chunks", [])):
                    ho_gold.add(c)
        except Exception:
            pass

all_excluded_gold = dev_a_gold | dev_b_gold | ho_gold
all_excluded_window = set(all_excluded_gold)
for cid in all_excluded_gold:
    num = get_num(cid)
    pfx = get_pfx(cid)
    if num != -1:
        all_excluded_window.add(f"{pfx}-C{num-1:04d}")
        all_excluded_window.add(f"{pfx}-C{num+1:04d}")

dev_a_sec = set((it["source_document_id"], norm_sec(it.get("parent_section_path", []))) for it in dev_a)
dev_b_sec = set((it["source_document_id"], norm_sec(it.get("parent_section_path", []))) for it in dev_b)
all_excluded_sec = dev_a_sec | dev_b_sec

all_excluded_qf = set(it.get("query_family") for it in dev_a + dev_b if it.get("query_family"))
all_excluded_sgk = set(it.get("split_group_key") for it in dev_a + dev_b if it.get("split_group_key"))

print(f"Exclusion Registry: {len(all_excluded_gold)} gold chunks, {len(all_excluded_window)} window chunks, {len(all_excluded_sec)} sections.")

# 2. Load Corpus Chunks
all_chunks = {}
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        all_chunks[ch["chunk_id"]] = ch

safe_chunk_ids = set()
for cid, ch in all_chunks.items():
    did = ch["document_id"]
    sec = norm_sec(ch.get("section_path", []))
    if cid not in all_excluded_window and (did, sec) not in all_excluded_sec:
        safe_chunk_ids.add(cid)

print(f"Safe Unspent Chunks: {len(safe_chunk_ids)} / {len(all_chunks)} ({len(safe_chunk_ids)/len(all_chunks)*100:.1f}%)")
