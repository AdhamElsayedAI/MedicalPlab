import json

data = json.load(open('reports/renal_v5/renal_v5_candidate_selector_dev_a_results.json', 'r', encoding='utf-8'))
naive_hits = {r['query_id']: r['hit_at_1'] for r in data['naive_top20']['query_records']}
b200_hits = {r['query_id']: r['hit_at_1'] for r in data['b200_to_r20']['query_records']}

gained = [qid for qid, h in b200_hits.items() if h and not naive_hits[qid]]
lost = [qid for qid, h in b200_hits.items() if not h and naive_hits[qid]]

print(f"Gained Hit@1 in B=200 ({len(gained)}): {gained}")
print(f"Lost Hit@1 in B=200 ({len(lost)}): {lost}")

for qid in gained:
    rec = next(r for r in data['b200_to_r20']['query_records'] if r['query_id'] == qid)
    print(f"  Gained [{qid}]: {rec['query']}")
    print(f"    Top1: {rec['top1_chunk_id']} (is_gold={rec['top1_is_gold']})")

# Let's check delta in Output Coverage @ 20:
naive_cov = {r['query_id']: r['relevant_in_r'] for r in data['naive_top20']['query_records']}
b200_cov = {r['query_id']: r['relevant_in_r'] for r in data['b200_to_r20']['query_records']}
cov_gained = [qid for qid, c in b200_cov.items() if c and not naive_cov[qid]]
cov_lost = [qid for qid, c in b200_cov.items() if not c and naive_cov[qid]]
print(f"\nCoverage@20 Gained ({len(cov_gained)}): {cov_gained}")
for qid in cov_gained:
    rec = next(r for r in data['b200_to_r20']['query_records'] if r['query_id'] == qid)
    print(f"  Cov Gained [{qid}]: {rec['query']}")
print(f"Coverage@20 Lost ({len(cov_lost)}): {cov_lost}")
for qid in cov_lost:
    rec = next(r for r in data['b200_to_r20']['query_records'] if r['query_id'] == qid)
    print(f"  Cov Lost [{qid}]: {rec['query']}")
