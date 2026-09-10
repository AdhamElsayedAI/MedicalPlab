"""Quick ablation + experiment summary printer."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

print("=" * 70)
print("EXPERIMENT MATRIX SUMMARY")
print("=" * 70)
exp = json.loads((ROOT / "reports" / "renal_v2_experiments.json").read_text())
print(f"Complete: {exp.get('complete')}  Model: {exp.get('model_id')}  Rev: {exp.get('model_revision', 'N/A')[:12]}")
print(f"Dataset SHA: {exp.get('dataset_sha256', 'N/A')[:16]}...")
print(f"{'Config':<35} {'Chunks':>7} {'H@1':>6} {'H@5':>6} {'H@10':>6} {'MRR':>7} {'nDCG@10':>9} {'GoldDoc@10':>11} {'Wall(s)':>8}")
for r in exp.get("results", []):
    m = r["metrics"]
    cfg = f"{r['chunking']} x {r['representation']}"
    print(f"{cfg:<35} {r['chunk_count']:>7} {m['hit_at_1']['value']:>6.4f} {m['hit_at_5']['value']:>6.4f} "
          f"{m['hit_at_10']['value']:>6.4f} {m['mrr']:>7.4f} {m['ndcg_at_10']:>9.4f} "
          f"{m['gold_source_recall_at_10']['value']:>11.4f} {r['elapsed_wall_seconds']:>8.1f}")

print()
print("=" * 70)
print("ABLATION STAGES SUMMARY")
print("=" * 70)
abl = json.loads((ROOT / "reports" / "renal_v2_ablation.json").read_text())
print(f"Dataset: {abl.get('dataset')}  N={abl.get('n_answerable')}")
print(f"Selected prompt: {abl.get('selected_prompt')}")
print(f"Selected RRF: {abl.get('selected_rrf')}")
print(f"Selected source prior: {abl.get('selected_source_prior')}")
reranker = abl.get('reranker', {})
print(f"Reranker: {reranker.get('model_id')} candidates={reranker.get('candidate_count')} generator={reranker.get('selected_candidate_generator')}")
print()
print(f"{'Stage':<45} {'H@1':>6} {'H@3':>6} {'H@5':>6} {'H@10':>6} {'MRR':>7} {'nDCG@10':>9}")
for s in abl.get("stages", []):
    m = s["metrics"]
    name = s["stage"][:45]
    print(f"{name:<45} {m['hit_at_1']['value']:>6.4f} {m['hit_at_3']['value']:>6.4f} "
          f"{m['hit_at_5']['value']:>6.4f} {m['hit_at_10']['value']:>6.4f} "
          f"{m['mrr']:>7.4f} {m['ndcg_at_10']:>9.4f}")
print()
print(f"Final failure breakdown: {abl.get('final_failure_breakdown')}")
print(f"Total failures (missing Top10): {len(abl.get('final_failures', []))}")
print()
print("RERANKER TRIALS:")
for t in abl.get("reranker_trials", []):
    m = t["metrics"]
    print(f"  {t['candidate_generator']}: H@1={m['hit_at_1']['value']:.4f} H@5={m['hit_at_5']['value']:.4f} "
          f"MRR={m['mrr']:.4f} nDCG={m['ndcg_at_10']:.4f} elapsed={t.get('elapsed_seconds',0):.1f}s")
