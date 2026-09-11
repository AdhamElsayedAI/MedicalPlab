"""
MedicalPlab Renal V5 — Curate High Coverage Clean Train Benchmark (N=80)
========================================================================
Builds queries for the 80 safe, disjoint chunks in selected_80_chunks_inspect.json.
Measures dense retrieval rank for each query and ensures high B=500 input coverage.
"""

import sys
import os
import re
import json
import hashlib
from pathlib import Path
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "Scripts"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import torch
from transformers import AutoModel, AutoTokenizer
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

inspect_data = json.loads(Path("Data/experiments/renal_v5/selected_80_chunks_inspect.json").read_text(encoding="utf-8"))
core_records = inspect_data["core"]
val_records = inspect_data["val"]

print(f"Loaded {len(core_records)} core chunks and {len(val_records)} val chunks.")

def clean_query_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s

def formulate_items(records, split_name, start_idx):
    items = []
    for offset, r in enumerate(records):
        cid = r["cid"]
        did = r["did"]
        strat = r["strat"]
        ch = all_chunks[cid]
        sec_path = ch.get("section_path", [])
        ch_sec = norm_sec(sec_path)
        orig_text = ch["text"]

        # Pick best sentence
        sents = [s.strip() for s in orig_text.replace("\n", " ").split(". ") if 35 < len(s.strip()) < 220]
        if not sents:
            sents = [orig_text[:140].strip()]
        
        # Pick the most medically informative sentence
        best_sent = sents[0]
        for s in sents:
            if any(w in s.lower() for w in ["patient", "therap", "mechanis", "inhibi", "increas", "decreas", "express", "protein", "secretion", "absorpt", "disease", "renal", "kidney", "function", "gfr", "patholog"]):
                best_sent = s
                break

        # Slice exact span from original chunk text
        # Clean text might differ slightly by whitespace; find exact substring in orig_text
        words_in_sent = [w for w in re.findall(r"[A-Za-z0-9\-]+", best_sent) if len(w) >= 4]
        match_pos = -1
        if len(words_in_sent) >= 2:
            sub = " ".join(words_in_sent[:3])
            match_pos = orig_text.find(sub)
        if match_pos == -1 and words_in_sent:
            match_pos = orig_text.find(words_in_sent[0])

        if match_pos != -1:
            st = orig_text.rfind(". ", 0, match_pos)
            st = st + 2 if st != -1 else 0
            en = orig_text.find(". ", match_pos)
            en = en + 1 if en != -1 else len(orig_text)
            span = orig_text[st:en].strip()
            if len(span) < 25:
                span = orig_text[max(0, match_pos-20):min(len(orig_text), match_pos+120)].strip()
        else:
            span = orig_text[:120].strip()

        assert span in orig_text, f"Span not in text for {cid}!"

        # Extract medical terms for query construction
        # Find nouns/medical entities
        cand_terms = [w for w in re.findall(r"\b[A-Za-z0-9\-]{4,}\b", best_sent) 
                      if w.lower() not in {"this", "that", "these", "those", "were", "been", "have", "with", "from", "which", "study", "their", "other", "also", "using", "shown", "data", "figure", "table", "results", "methods", "between", "after", "before", "during", "suggesting", "demonstrated"}]

        term_head = " ".join(cand_terms[:3]) if cand_terms else "renal transport"
        
        # Formulate query using clinical question patterns
        if any(w in best_sent.lower() for w in ["inhibit", "block", "antagonist", "suppress"]):
            query = f"How does inhibition or antagonism of {term_head} influence renal pathophysiology?"
        elif any(w in best_sent.lower() for w in ["treatment", "therap", "drug", "dose", "administer"]):
            query = f"What clinical therapeutic role does {term_head} serve in renal management?"
        elif any(w in best_sent.lower() for w in ["mutation", "gene", "defect", "knockout", "deficien"]):
            query = f"What functional defect or disease results from genetic alteration in {term_head}?"
        elif any(w in best_sent.lower() for w in ["excret", "absorp", "transport", "reabsorp", "channel", "cotransport"]):
            query = f"What is the mechanism of tubular transport and handling of {term_head}?"
        elif any(w in best_sent.lower() for w in ["marker", "diagnos", "detect", "biomarker", "sediment", "urinalysis"]):
            query = f"How is {term_head} utilized as a diagnostic indicator in kidney disease?"
        else:
            query = f"What is the clinical and physiological significance of {term_head} in renal medicine?"

        claim = f"Evidence indicates that {best_sent.strip()}."
        obj = f"Understand the clinical and physiological role of {term_head} in renal medicine"
        
        qid_num = start_idx + offset
        qid_str = f"V5-RNK-TRAIN-{qid_num:04d}"

        qf_hash = hashlib.sha256(f"{did}|{ch_sec}|{norm(query)}".encode()).hexdigest()[:12]
        sgk_hash = hashlib.sha256(f"{did}|{ch_sec}".encode()).hexdigest()[:12]

        items.append({
            "query_id": qid_str,
            "query": clean_query_text(query),
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
            "qrel_support_rationale": f"Passage directly documents that: {span[:140]}...",
            "qrel_construction_method": "SOURCE_GROUNDED_SPAN_VERIFICATION",
            "verification_status": "VERIFIED_SAFE_UNSPENT",
            "query_family": f"QF-{strat}-{did}-{qf_hash}",
            "split_group_key": sgk_hash,
            "source": "V5_TRAIN_CLEAN_V1",
            "split": split_name
        })
    return items

core_items = formulate_items(core_records, "core", 1)
val_items = formulate_items(val_records, "val", 61)
all_items = core_items + val_items

print(f"Generated 80 items. Auditing dense ranks...")
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
print(f"Top 20 Coverage: CORE = {(core_arr <= 20).sum()}/60, VAL = {(val_arr <= 20).sum()}/20")
