import json

with open('evaluation/renal/v5/renal-rerank-dev-a-v5.json', 'r', encoding='utf-8') as f:
    dev_a = json.load(f)

print(f"Total DEV-A items: {len(dev_a)}")
non_auto = []
for i, it in enumerate(dev_a):
    gold = it.get('gold_chunk_ids', [])
    status = it.get('review_status', 'UNKNOWN')
    if len(gold) == 0 or status != 'AUTO_VERIFIED':
        non_auto.append((i, it['query_id'], len(gold), status, it['query']))

print(f"Non-auto / empty gold items in DEV-A: {len(non_auto)}")
for item in non_auto:
    print(f"  Item {item[0]}: {item[1]} gold_len={item[2]} status={item[3]} query='{item[4]}'")
