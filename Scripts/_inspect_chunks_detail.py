import json
from pathlib import Path

chunks = json.loads(Path('scratch/all_80_chunks_full.json').read_text(encoding='utf-8'))

with open('scratch/chunks_preview.txt', 'w', encoding='utf-8') as f:
    for i, c in enumerate(chunks):
        f.write(f"=== [{i:02d}] {c['split'].upper()} | {c['cid']} | {c['strat']} | {c['did']} ===\n")
        f.write(f"Section: {' > '.join(c['sec']) if isinstance(c['sec'], list) else c['sec']}\n")
        f.write(f"Text snippet (first 300 chars):\n{c['text'][:300]}\n\n")

print(f"Wrote preview for {len(chunks)} chunks to scratch/chunks_preview.txt")
