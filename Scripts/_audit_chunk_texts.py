import json
from pathlib import Path

data = json.loads(Path('scratch/all_80_chunks_full.json').read_text(encoding='utf-8'))

# Flag any chunks that look like figure captions, western blots, or meta text
issues = []
for i, item in enumerate(data):
    text = item['text']
    sec = ' > '.join(item['sec']) if isinstance(item['sec'], list) else item['sec']
    cid = item['cid']
    split = item['split']
    strat = item['strat']
    
    flag = None
    if 'western blot' in text.lower() or 'cropped' in text.lower():
        flag = 'WESTERN_BLOT'
    elif 'pubmed was searched' in text.lower():
        flag = 'PUBMED_SEARCH'
    elif len(text.strip()) < 200:
        flag = 'TOO_SHORT'
    elif text.count(';') > 10 and text.count(':') > 5:
        flag = 'TABLE_LIKE'
    
    if flag:
        issues.append((i, split, strat, cid, sec, flag, text[:120]))

print(f"Total flagged chunks: {len(issues)} / 80")
for iss in issues:
    print(iss)
