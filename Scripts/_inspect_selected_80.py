import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

import json
from _test_grounded_pool_builder import core_cands, val_cands
from build_clean_train_v1 import all_chunks, norm_sec

print(f"Total core: {len(core_cands)}, Total val: {len(val_cands)}")

out = {"core": [], "val": []}
for strat, c in core_cands:
    cid = c["chunk_id"]
    ch = all_chunks[cid]
    sents = [s.strip() for s in ch["text"].replace("\n", " ").split(". ") if 40 < len(s.strip()) < 200]
    out["core"].append({
        "strat": strat,
        "cid": cid,
        "did": c["document_id"],
        "sec": ch.get("section_path", []),
        "sents": sents[:3]
    })

for strat, c in val_cands:
    cid = c["chunk_id"]
    ch = all_chunks[cid]
    sents = [s.strip() for s in ch["text"].replace("\n", " ").split(". ") if 40 < len(s.strip()) < 200]
    out["val"].append({
        "strat": strat,
        "cid": cid,
        "did": c["document_id"],
        "sec": ch.get("section_path", []),
        "sents": sents[:3]
    })

Path("Data/experiments/renal_v5/selected_80_chunks_inspect.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
print("Saved selected 80 chunks inspect file.")
