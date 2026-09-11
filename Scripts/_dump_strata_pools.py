import json
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from mine_rich_safe_curriculum import get_candidates
from build_clean_train_v1 import all_chunks, norm_sec

pools = get_candidates()

out_summary = {}
for strat, cands in sorted(pools.items()):
    out_summary[strat] = []
    # Pick top 15 distinct sections
    seen_sec = set()
    for c in cands:
        cid = c["chunk_id"]
        did = c["document_id"]
        ch = all_chunks[cid]
        sec = norm_sec(ch.get("section_path", []))
        if sec in seen_sec: continue
        seen_sec.add(sec)
        
        # Grab first 2 sentences
        text = ch["text"].replace("\n", " ")
        sents = [s.strip() for s in text.split(". ") if 30 < len(s.strip()) < 200]
        if len(sents) >= 2:
            out_summary[strat].append({
                "cid": cid,
                "did": did,
                "sec": ch.get("section_path", []),
                "sents": sents[:3]
            })
        if len(out_summary[strat]) >= 12:
            break

Path("Data/experiments/renal_v5/strata_curriculum_pools.json").write_text(
    json.dumps(out_summary, indent=2), encoding="utf-8"
)
print("Saved strata curriculum pools for 12 strata.")
