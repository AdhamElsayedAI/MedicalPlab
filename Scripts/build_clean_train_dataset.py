"""
MedicalPlab Renal V5 — Construct Clean Train V1 Benchmark (N=80)
================================================================
Generates 80 fully source-grounded, verified items from safe unspent corpus chunks.
Guarantees 100% verification that each supporting evidence span exists in chunk text.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "Scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import (
    all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, 
    norm, norm_sec, OUT_CLEAN_TRAIN
)
from mine_exact_safe_spans import mine_candidates

# Strategy: For each stratum, pick the specified number of distinct, high-quality candidates
QUOTAS = {
    "STR-01": 7, "STR-02": 7, "STR-03": 6, "STR-04": 6,
    "STR-05": 7, "STR-06": 6, "STR-07": 7, "STR-08": 7,
    "STR-09": 7, "STR-10": 6, "STR-11": 7, "STR-12": 7
}

STRAT_NAMES = {
    "STR-01": "glomerular filtration and hemodynamics",
    "STR-02": "tubular transport and processing",
    "STR-03": "medullary concentration and water handling",
    "STR-04": "renal endocrine systems and regulation",
    "STR-05": "potassium and electrolyte homeostasis",
    "STR-06": "acid-base balance and buffer regulation",
    "STR-07": "acute kidney injury pathophysiology",
    "STR-08": "chronic kidney disease and progression",
    "STR-09": "glomerular diseases and nephrotic syndromes",
    "STR-10": "tubulointerstitial and infectious renal disorders",
    "STR-11": "nephrolithiasis and mineral metabolism",
    "STR-12": "renal replacement therapy and transplantation"
}

STYLES = ["QS-ROLE", "QS-MECH", "QS-IMPACT", "QS-DIST", "QS-REG", "QS-CLIN", "QS-PATH"]

def clean_span(s):
    # Ensure span is an exact substring in chunk['text']
    return s.strip()

def build_items():
    cands = mine_candidates()
    items = []
    global_idx = 1
    seen_queries = set()
    core_chunks = set()
    core_windows = set()
    core_sections = set()
    val_chunks = set()
    val_windows = set()
    val_sections = set()

    # Pre-select disjoint sets for all strata
    stratum_selections = {}

    for strat, quota in QUOTAS.items():
        strat_cands = cands[strat]
        n_core = 5
        n_val = quota - n_core
        
        selected_core = []
        selected_val = []
        seen_terms = set()

        # Pass 1: Select n_core for CORE
        for c in strat_cands:
            cid = c["chunk_id"]
            did = c["document_id"]
            term = c["term"]
            ch = all_chunks[cid]
            sec = norm_sec(ch.get("section_path", []))

            if term.lower() in seen_terms:
                continue
            if cid in core_chunks or cid in core_windows or cid in val_chunks or cid in val_windows:
                continue
            if (did, sec) in val_sections or (did, sec) in core_sections:
                continue
            assert cid in safe_chunk_ids and cid not in all_excluded_window
            assert (did, sec) not in all_excluded_sec

            # Slice invariant
            text = ch["text"]
            pos = text.lower().find(term.lower())
            if pos == -1: continue
            start = text.rfind(". ", 0, pos)
            start = start + 2 if start != -1 else 0
            end = text.find(". ", pos)
            end = end + 1 if end != -1 else len(text)
            span = text[start:end].strip()
            if len(span) < 30:
                span = text[max(0, pos-40):min(len(text), pos+140)].strip()
            assert span in text

            selected_core.append((c, span))
            seen_terms.add(term.lower())
            core_chunks.add(cid)
            num = int(re.search(r"-C(\d+)$", cid).group(1))
            pfx = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid).group(1)
            core_windows.add(f"{pfx}-C{num-1:04d}")
            core_windows.add(f"{pfx}-C{num:04d}")
            core_windows.add(f"{pfx}-C{num+1:04d}")
            core_sections.add((did, sec))

            if len(selected_core) == n_core:
                break

        assert len(selected_core) == n_core, f"Could not satisfy core quota {n_core} for {strat}! Got {len(selected_core)}"

        # Pass 2: Select n_val for VAL
        for c in strat_cands:
            cid = c["chunk_id"]
            did = c["document_id"]
            term = c["term"]
            ch = all_chunks[cid]
            sec = norm_sec(ch.get("section_path", []))

            if term.lower() in seen_terms:
                continue
            if cid in core_chunks or cid in core_windows or cid in val_chunks or cid in val_windows:
                continue
            if (did, sec) in core_sections:
                continue
            assert cid in safe_chunk_ids and cid not in all_excluded_window
            assert (did, sec) not in all_excluded_sec

            # Slice invariant
            text = ch["text"]
            pos = text.lower().find(term.lower())
            if pos == -1: continue
            start = text.rfind(". ", 0, pos)
            start = start + 2 if start != -1 else 0
            end = text.find(". ", pos)
            end = end + 1 if end != -1 else len(text)
            span = text[start:end].strip()
            if len(span) < 30:
                span = text[max(0, pos-40):min(len(text), pos+140)].strip()
            assert span in text

            selected_val.append((c, span))
            seen_terms.add(term.lower())
            val_chunks.add(cid)
            num = int(re.search(r"-C(\d+)$", cid).group(1))
            pfx = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid).group(1)
            val_windows.add(f"{pfx}-C{num-1:04d}")
            val_windows.add(f"{pfx}-C{num:04d}")
            val_windows.add(f"{pfx}-C{num+1:04d}")
            val_sections.add((did, sec))

            if len(selected_val) == n_val:
                break

        assert len(selected_val) == n_val, f"Could not satisfy val quota {n_val} for {strat}! Got {len(selected_val)}"
        stratum_selections[strat] = selected_core + selected_val

    for strat, quota in QUOTAS.items():
        selected_for_strat = stratum_selections[strat]
        
        strat_display = STRAT_NAMES.get(strat, "renal medicine")
        for i, (cand, span) in enumerate(selected_for_strat):
            cid = cand["chunk_id"]
            did = cand["document_id"]
            term = cand["term"]
            sec_path = cand["section_path"]
            ch_sec = norm_sec(sec_path)
            style = STYLES[i % len(STYLES)]
            
            # Generate clean educational query based on stratum and term
            qid_str = f"V5-RNK-TRAIN-{global_idx:04d}"
            
            if style == "QS-ROLE":
                query = f"What is the physiological role of {term} in {strat_display}?"
            elif style == "QS-MECH":
                query = f"Explain the mechanism by which {term} functions in renal pathophysiology."
            elif style == "QS-IMPACT":
                query = f"How does {term} influence renal tubular and glomerular outcomes?"
            elif style == "QS-DIST":
                query = f"What distinguishes {term} in renal diagnostic evaluation and clinical care?"
            elif style == "QS-REG":
                query = f"How is {term} regulated in maintaining renal homeostasis?"
            elif style == "QS-CLIN":
                query = f"What clinical consequence is associated with alterations in {term}?"
            elif style == "QS-PATH":
                query = f"In what way does {term} contribute to renal disease progression?"
            else:
                query = f"What is the clinical significance of {term} in {strat_display}?"

            # Craft grounded claim directly using the evidence span
            claim = f"Evidence shows that {span[:180].strip()}."
            objective = f"Understand the clinical and physiological role of {term} in {strat_display}"
            rationale = f"Passage directly documents that: {span[:140]}..."
            
            q_norm = norm(query)
            if q_norm in seen_queries:
                query = f"How does {term} function in {strat_display} (context {global_idx})?"
                q_norm = norm(query)
            seen_queries.add(q_norm)
            
            qf_hash = hashlib.sha256(f"{did}|{ch_sec}|{q_norm}".encode()).hexdigest()[:12]
            sgk_hash = hashlib.sha256(f"{did}|{ch_sec}".encode()).hexdigest()[:12]
            
            item = {
                "query_id": qid_str,
                "query": query,
                "curriculum_stratum": strat,
                "query_style": style,
                "learning_objective": objective,
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
                "source": "V5_TRAIN_CLEAN_V1"
            }
            items.append(item)
            global_idx += 1
            
    return items

def main():
    print("=" * 80)
    print("CONSTRUCTING CLEAN TRAIN V1 DATASET (N=80)")
    print("=" * 80)
    
    clean_items = build_items()
    assert len(clean_items) == 80, f"Expected 80, got {len(clean_items)}"
    
    # Verify all invariants
    for it in clean_items:
        cid = it["gold_chunk_ids"][0]
        assert cid in safe_chunk_ids, f"Chunk {cid} not in safe set!"
        assert cid not in all_excluded_window, f"Chunk {cid} in excluded window!"
        ch = all_chunks[cid]
        assert (it["source_document_id"], norm_sec(it["parent_section_path"])) not in all_excluded_sec
        assert it["evidence_span_text"] in ch["text"], f"Span not in chunk text for {it['query_id']}!"

    # Save to file
    clean_bytes = json.dumps(clean_items, indent=2, ensure_ascii=False).encode("utf-8")
    OUT_CLEAN_TRAIN.write_bytes(clean_bytes)
    clean_sha = hashlib.sha256(clean_bytes).hexdigest()
    
    sidecar_path = OUT_CLEAN_TRAIN.parent / f"{OUT_CLEAN_TRAIN.name}.sha256"
    sidecar_path.write_text(f"{clean_sha}  {OUT_CLEAN_TRAIN.name}\n", encoding="utf-8")
    
    print(f"CLEAN TRAIN V1 SUCCESS:")
    print(f"Path:   {OUT_CLEAN_TRAIN}")
    print(f"SHA256: {clean_sha}")
    print(f"Total items: {len(clean_items)}")

if __name__ == "__main__":
    main()
