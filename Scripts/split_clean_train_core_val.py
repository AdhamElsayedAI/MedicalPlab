"""
MedicalPlab Renal V5 — Split Clean Train V1 into CORE (N=60) and VAL (N=20)
============================================================================
Enforces complete disjointness between TRAIN_CORE and TRAIN_VAL:
- Query IDs
- Canonical claims
- Evidence-span chunks (+/- 1 window)
- Normalized source-section identity
- Query families and transformation keys
"""

import hashlib
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
CLEAN_TRAIN_PATH = _ROOT / "evaluation/renal/v5/renal-rerank-train-v5-clean-v1.json"
OUT_CORE_PATH = _ROOT / "evaluation/renal/v5/renal-rerank-train-core-v5-clean-v1.json"
OUT_VAL_PATH = _ROOT / "evaluation/renal/v5/renal-rerank-train-val-v5-clean-v1.json"

def norm_sec(p):
    if not p: return ""
    if isinstance(p, list): return " > ".join(s.strip().lower() for s in p)
    return str(p).strip().lower()

def get_num(cid: str) -> int:
    m = re.search(r"-C(\d+)$", cid)
    return int(m.group(1)) if m else -1

def get_pfx(cid: str) -> str:
    m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
    return m.group(1) if m else cid

def expand_chunks(cids):
    res = set()
    for cid in cids:
        pfx = get_pfx(cid)
        num = get_num(cid)
        if num != -1:
            res.add(f"{pfx}-C{num:04d}")
            res.add(f"{pfx}-C{num-1:04d}")
            res.add(f"{pfx}-C{num+1:04d}")
    return res

def main():
    print("=" * 80)
    print("SPLITTING CLEAN TRAIN V1 INTO CORE (N=60) AND VAL (N=20)")
    print("=" * 80)

    clean_items = json.loads(CLEAN_TRAIN_PATH.read_text(encoding="utf-8"))
    assert len(clean_items) == 80

    by_stratum = {}
    for it in clean_items:
        s = it["curriculum_stratum"]
        by_stratum.setdefault(s, []).append(it)

    core_items = []
    val_items = []

    for strat in sorted(by_stratum.keys()):
        items = by_stratum[strat]
        # First 5 items go to CORE, remainder go to VAL
        core_subset = items[:5]
        val_subset = items[5:]
        assert len(core_subset) == 5
        assert len(val_subset) in [1, 2]
        core_items.extend(core_subset)
        val_items.extend(val_subset)

    assert len(core_items) == 60
    assert len(val_items) == 20

    # Internal Firewall Verification: CORE vs VAL
    print("\nVerifying Internal Disjointness (CORE vs VAL)...")

    # 1. Query IDs
    core_qids = set(it["query_id"] for it in core_items)
    val_qids = set(it["query_id"] for it in val_items)
    assert len(core_qids & val_qids) == 0, "Query ID overlap!"

    # 2. Canonical claims
    core_claims = set(it["canonical_claim"].strip().lower() for it in core_items)
    val_claims = set(it["canonical_claim"].strip().lower() for it in val_items)
    assert len(core_claims & val_claims) == 0, "Canonical claim overlap!"

    # 3. Chunks and adjacent windows
    core_chunks = set(c for it in core_items for c in it.get("gold_chunk_ids", []))
    val_chunks = set(c for it in val_items for c in it.get("gold_chunk_ids", []))
    assert len(core_chunks & val_chunks) == 0, "Chunk overlap!"

    core_win = expand_chunks(core_chunks)
    val_win = expand_chunks(val_chunks)
    assert len(core_win & val_chunks) == 0, "Window overlap with VAL chunks!"
    assert len(val_win & core_chunks) == 0, "Window overlap with CORE chunks!"

    # 4. Source sections
    core_secs = set((it["source_document_id"], norm_sec(it["parent_section_path"])) for it in core_items)
    val_secs = set((it["source_document_id"], norm_sec(it["parent_section_path"])) for it in val_items)
    assert len(core_secs & val_secs) == 0, "Source section overlap between CORE and VAL!"

    # 5. Query family and split group key
    core_qf = set(it["query_family"] for it in core_items)
    val_qf = set(it["query_family"] for it in val_items)
    assert len(core_qf & val_qf) == 0, "Query family overlap!"

    core_sgk = set(it["split_group_key"] for it in core_items)
    val_sgk = set(it["split_group_key"] for it in val_items)
    assert len(core_sgk & val_sgk) == 0, "Split group key overlap!"

    print("INTERNAL FIREWALL: 100% DISJOINT across queries, claims, chunks, sections, and template families.")

    # Persist CORE
    core_bytes = json.dumps(core_items, indent=2, ensure_ascii=False).encode("utf-8")
    OUT_CORE_PATH.write_bytes(core_bytes)
    core_sha = hashlib.sha256(core_bytes).hexdigest()
    (OUT_CORE_PATH.parent / f"{OUT_CORE_PATH.name}.sha256").write_text(f"{core_sha}  {OUT_CORE_PATH.name}\n", encoding="utf-8")

    # Persist VAL
    val_bytes = json.dumps(val_items, indent=2, ensure_ascii=False).encode("utf-8")
    OUT_VAL_PATH.write_bytes(val_bytes)
    val_sha = hashlib.sha256(val_bytes).hexdigest()
    (OUT_VAL_PATH.parent / f"{OUT_VAL_PATH.name}.sha256").write_text(f"{val_sha}  {OUT_VAL_PATH.name}\n", encoding="utf-8")

    print(f"\nCORE Artifact: {OUT_CORE_PATH}")
    print(f"CORE SHA256:  {core_sha}")
    print(f"VAL Artifact:  {OUT_VAL_PATH}")
    print(f"VAL SHA256:   {val_sha}")

if __name__ == "__main__":
    main()
