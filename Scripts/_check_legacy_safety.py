import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))
from build_clean_train_v1 import safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec

legacy = json.loads((_ROOT / "evaluation/renal/v5/renal-rerank-train-v5-extended.json").read_text(encoding="utf-8"))
clean_legacy_ids = [
    'V5-RNK-TRAIN-0001', 'V5-RNK-TRAIN-0002', 'V5-RNK-TRAIN-0003', 'V5-RNK-TRAIN-0004',
    'V5-RNK-TRAIN-0005', 'V5-RNK-TRAIN-0007', 'V5-RNK-TRAIN-0009', 'V5-RNK-TRAIN-0013',
    'V5-RNK-TRAIN-0015', 'V5-RNK-TRAIN-0017', 'V5-RNK-TRAIN-0018', 'V5-RNK-TRAIN-0019', 'V5-RNK-TRAIN-0020'
]

safe_count = 0
for it in legacy[:20]:
    qid = it['query_id']
    if qid in clean_legacy_ids:
        cids = it['gold_chunk_ids']
        sec = (it['source_document_id'], norm_sec(it.get('parent_section_path', [])))
        all_safe = all(c in safe_chunk_ids for c in cids)
        no_win = all(c not in all_excluded_window for c in cids)
        sec_safe = sec not in all_excluded_sec
        is_safe = all_safe and no_win and sec_safe
        if is_safe:
            safe_count += 1
        print(f"{qid} ({it['curriculum_stratum']}): chunks_safe={all_safe}, no_win={no_win}, sec_safe={sec_safe} -> SAFE={is_safe}")
        print(f"  Q: {it['query']}")

print(f"\nSafe items out of 13: {safe_count}/13")
