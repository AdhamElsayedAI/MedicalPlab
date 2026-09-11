import json

data = json.load(open('reports/renal_v5/renal_v5_safe_rescue_dev_a_results.json', 'r', encoding='utf-8'))
for r in data['query_records']:
    if not r['has_in_naive'] and r['has_in_r']:
        print(f"RESCUED: {r['query_id']} | {r['query']}")
        print(f"  Hit@1: {r['hit_at_1']}, Top1 Chunk: {r['top1_chunk_id']}")
    elif r['has_in_naive'] and not r['has_in_r']:
        print(f"LOST: {r['query_id']} | {r['query']}")
