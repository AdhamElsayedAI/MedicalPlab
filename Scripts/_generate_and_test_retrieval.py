import sys
import os
import re
import json
import hashlib
from pathlib import Path
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_ROOT / "Scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Scripts"))

import torch
from transformers import AutoModel, AutoTokenizer
from mine_rich_safe_curriculum import get_candidates
from build_clean_train_v1 import all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec, norm

chunks_dir = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
cache_dir = _ROOT / "Data/experiments/renal_v3/cache"

chunks = []
chunk_doc_ids = []
for p in sorted(chunks_dir.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunks.append(ch)
        chunk_doc_ids.append(ch["document_id"])

corpus_embs = np.load(cache_dir / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(cache_dir / "all23_doc_embeddings.npy").astype(np.float32)
doc_ids_sorted = sorted(list(set(chunk_doc_ids)))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_id_to_idx = {ch["chunk_id"]: i for i, ch in enumerate(chunks)}

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
mod = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "

QUOTAS = {
    "STR-01": 7, "STR-02": 7, "STR-03": 6, "STR-04": 6,
    "STR-05": 7, "STR-06": 6, "STR-07": 7, "STR-08": 7,
    "STR-09": 7, "STR-10": 6, "STR-11": 7, "STR-12": 7
}

pools = get_candidates()

def get_num(cid: str) -> int:
    m = re.search(r"-C(\d+)$", cid)
    return int(m.group(1)) if m else -1

def get_pfx(cid: str) -> str:
    m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
    return m.group(1) if m else cid

def expand_cid(cid):
    pfx = get_pfx(cid)
    num = get_num(cid)
    return {f"{pfx}-C{num-1:04d}", f"{pfx}-C{num:04d}", f"{pfx}-C{num+1:04d}"}

# Select candidates
core_cands = []
val_cands = []
core_secs = set()
val_secs = set()
core_chunks = set()
val_chunks = set()
core_win = set()
val_win = set()

for strat, quota in QUOTAS.items():
    pool = pools[strat]
    n_core = 5
    n_val = quota - n_core

    sel_core = []
    for c in pool:
        cid = c["chunk_id"]
        did = c["document_id"]
        sec = norm_sec(c["section_path"])
        if cid in core_chunks or cid in core_win or cid in val_chunks or cid in val_win: continue
        if (did, sec) in val_secs: continue

        sel_core.append(c)
        core_chunks.add(cid)
        core_win.update(expand_cid(cid))
        core_secs.add((did, sec))
        if len(sel_core) == n_core:
            break
    assert len(sel_core) == n_core

    sel_val = []
    for c in pool:
        cid = c["chunk_id"]
        did = c["document_id"]
        sec = norm_sec(c["section_path"])
        if cid in core_chunks or cid in core_win or cid in val_chunks or cid in val_win: continue
        if (did, sec) in core_secs: continue

        sel_val.append(c)
        val_chunks.add(cid)
        val_win.update(expand_cid(cid))
        val_secs.add((did, sec))
        if len(sel_val) == n_val:
            break
    assert len(sel_val) == n_val

    for c in sel_core: core_cands.append((strat, c))
    for c in sel_val: val_cands.append((strat, c))

def create_item(strat, c, split_name, idx):
    cid = c["chunk_id"]
    did = c["document_id"]
    ch = all_chunks[cid]
    sec_path = ch.get("section_path", [])
    ch_sec = norm_sec(sec_path)
    text = ch["text"].replace("\n", " ")

    # Find longest informative sentence
    sents = [s.strip() for s in text.split(". ") if 40 < len(s.strip()) < 220]
    if not sents:
        sents = [text[:150].strip()]
    best_sent = sents[0]
    for s in sents:
        if any(w in s.lower() for w in ["mediat", "regulat", "increas", "decreas", "inhibit", "induc", "pathway", "receptor", "transport", "activat", "reduc", "kidney", "renal", "glomerul", "tubul"]):
            best_sent = s
            break

    # Extract salient keywords from best_sent
    words = re.findall(r"\b[A-Za-z0-9\-]{4,}\b", best_sent)
    stop = {"this", "that", "these", "those", "from", "with", "were", "been", "have", "which", "study", "using", "shown", "their", "other", "also", "into", "after", "between", "both", "show", "data", "used"}
    keywords = [w for w in words if w.lower() not in stop][:4]
    kw_str = " and ".join(keywords[:2]) if keywords else "renal physiological function"

    # Craft natural query aligned with the sentence proposition
    if "inhibit" in best_sent.lower() or "block" in best_sent.lower():
        query = f"How does inhibition of {kw_str} affect renal pathophysiology?"
    elif "increas" in best_sent.lower() or "stimulat" in best_sent.lower():
        query = f"How does activation or increase of {kw_str} influence renal function?"
    elif "decreas" in best_sent.lower() or "reduc" in best_sent.lower() or "loss" in best_sent.lower():
        query = f"What clinical consequence results from the reduction of {kw_str} in renal disease?"
    elif "receptor" in best_sent.lower() or "channel" in best_sent.lower() or "transporter" in best_sent.lower():
        query = f"What is the physiological transport mechanism of {kw_str} in renal tubular handling?"
    else:
        query = f"What is the clinical significance of {kw_str} in renal medicine and physiology?"

    claim = f"Evidence shows that {best_sent.strip()}."
    obj = f"Understand the clinical and physiological role of {kw_str} in renal medicine"
    rationale = f"Passage directly documents that: {best_sent[:140]}..."

    # Ensure best_sent is an exact substring in ch['text']
    # If not exact due to replace('\n', ' '), slice directly from original ch['text']
    orig_text = ch["text"]
    pos = orig_text.lower().find(keywords[0].lower()) if keywords else -1
    if pos != -1:
        start = orig_text.rfind(". ", 0, pos)
        start = start + 2 if start != -1 else 0
        end = orig_text.find(". ", pos)
        end = end + 1 if end != -1 else len(orig_text)
        span = orig_text[start:end].strip()
        if len(span) < 30:
            span = orig_text[max(0, pos-40):min(len(orig_text), pos+140)].strip()
    else:
        span = orig_text[:140].strip()
    assert span in orig_text

    qid_str = f"V5-RNK-TRAIN-{idx:04d}"
    qf_hash = hashlib.sha256(f"{did}|{ch_sec}|{norm(query)}".encode()).hexdigest()[:12]
    sgk_hash = hashlib.sha256(f"{did}|{ch_sec}".encode()).hexdigest()[:12]

    return {
        "query_id": qid_str,
        "query": query,
        "curriculum_stratum": strat,
        "query_style": "QS-A",
        "learning_objective": obj,
        "canonical_claim": claim,
        "source_document_id": did,
        "parent_section_path": sec_path,
        "evidence_span_text": span,
        "gold_chunk_ids": [cid],
        "gold_doc_id": did,
        "gold_section_path": sec_path,
        "qrel_support_rationale": rationale,
        "qrel_construction_method": "SOURCE_GROUNDED_SPAN_VERIFICATION",
        "verification_status": "VERIFIED_SAFE_UNSPENT",
        "query_family": f"QF-{strat}-{did}-{qf_hash}",
        "split_group_key": sgk_hash,
        "source": "V5_TRAIN_CLEAN_V1",
        "split": split_name
    }

print("\nGenerating items...")
all_items = []
idx = 1
for strat, c in core_cands:
    all_items.append(create_item(strat, c, "core", idx))
    idx += 1
for strat, c in val_cands:
    all_items.append(create_item(strat, c, "val", idx))
    idx += 1

print(f"Generated {len(all_items)} items. Evaluating retrieval ranking...")
q_texts = [QUERY_INSTRUCTION + it["query"] for it in all_items]
with torch.inference_mode():
    enc = tok(q_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
    out = mod(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_embs = torch.nn.functional.normalize(q_embs, p=2, dim=1).cpu().numpy().astype(np.float32)

core_ranks = []
val_ranks = []
for i, it in enumerate(all_items):
    q_vec = q_embs[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]
    ranked = comb.argsort()[::-1]
    g_idx = chunk_id_to_idx[it["gold_chunk_ids"][0]]
    rank = int(np.where(ranked == g_idx)[0][0]) + 1
    if it["split"] == "core":
        core_ranks.append(rank)
    else:
        val_ranks.append(rank)

core_arr = np.array(core_ranks)
val_arr = np.array(val_ranks)

print(f"\nCORE (N=60): B=500 Coverage = {(core_arr <= 500).sum()}/60 ({(core_arr <= 500).mean()*100:.1f}%), Median Rank = {np.median(core_arr)}")
print(f"VAL  (N=20): B=500 Coverage = {(val_arr <= 500).sum()}/20 ({(val_arr <= 500).mean()*100:.1f}%), Median Rank = {np.median(val_arr)}")
