import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from mine_exact_safe_spans import mine_candidates, STRATUM_SEARCH

cands = mine_candidates()
for s, it in cands.items():
    terms = sorted(list(set(c["term"] for c in it)))
    print(f"{s}: {len(it)} chunks, {len(terms)} distinct terms: {terms}")
