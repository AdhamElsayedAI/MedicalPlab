import json
from pathlib import Path
from collections import defaultdict

data = json.loads(Path('scratch/all_80_chunks_full.json').read_text(encoding='utf-8'))

# Group by stratum
strata = defaultdict(list)
for item in data:
    strata[item['strat']].append(item)

with open('scratch/strata_curation_guide.txt', 'w', encoding='utf-8') as f:
    for strat in sorted(strata.keys()):
        f.write(f"\n======================================================================\n")
        f.write(f"STRATUM: {strat} ({len(strata[strat])} items)\n")
        f.write(f"======================================================================\n")
        for item in strata[strat]:
            f.write(f"\n--- [{item['split'].upper()}] {item['cid']} ({item['did']}) ---\n")
            f.write(f"Section: {' > '.join(item['sec']) if isinstance(item['sec'], list) else item['sec']}\n")
            # Print first 4 sentences
            sents = [s.strip() for s in item['text'].replace('\n', ' ').split('. ') if len(s.strip()) > 30]
            for s_idx, s in enumerate(sents[:4]):
                f.write(f"  [S{s_idx}] {s}.\n")

print("Wrote curation guide to scratch/strata_curation_guide.txt")
