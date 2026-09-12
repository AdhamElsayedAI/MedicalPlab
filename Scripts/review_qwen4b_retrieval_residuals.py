from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from qwen4b_adaptation_common import load_config, root_path, resolve_corpus_dir, load_chunks, atomic_json


def _index_by_query_id(items):
    return {str(x.get('query_id')): x for x in items if x.get('query_id')}


def main(cfg):
    report_path = root_path(cfg['outputs']['evaluation_report'])
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('gate', {}).get('passed') is not False:
        raise RuntimeError('RESIDUAL_REVIEW_REQUIRES_FAILED_RETRIEVAL_GATE')

    items = json.loads(root_path(cfg['data']['product_dev_v3']).read_text(encoding='utf-8'))
    by_id = _index_by_query_id(items)
    chunks, _ = load_chunks(resolve_corpus_dir(cfg))

    residuals = report.get('residual_failures', [])
    detailed = []
    for r in residuals:
        qid = str(r['query_id'])
        it = by_id.get(qid)
        if not it:
            raise RuntimeError(f'PRODUCT_DEV_QUERY_MISSING query_id={qid}')
        support = list(it.get('semantic_support_chunk_ids', it.get('exact_gold_chunk_ids', [])))
        exact = list(it.get('exact_gold_chunk_ids', []))
        missing_support = [cid for cid in support if cid not in chunks]
        support_preview = []
        for cid in support:
            ch = chunks.get(cid)
            support_preview.append({
                'chunk_id': cid,
                'present_in_corpus': ch is not None,
                'text_preview': (ch.get('text', '')[:280] if ch else None),
                'document_id': (ch.get('document_id') if ch else None),
                'section_path': (ch.get('section_path') if ch else None),
            })
        detailed.append({
            'query_id': qid,
            'query': it.get('query'),
            'canonical_claim': it.get('canonical_claim'),
            'learning_objective': it.get('learning_objective'),
            'curriculum_category': it.get('curriculum_category'),
            'gold_document_id': it.get('gold_document_id'),
            'rank': r.get('rank'),
            'category': r.get('category'),
            'exact_gold_chunk_ids': exact,
            'semantic_support_chunk_ids': support,
            'missing_support_chunk_ids': missing_support,
            'support_chunk_previews': support_preview,
        })

    n = int(report.get('n_queries', len(items)))
    fail50 = len(residuals)
    inferred_r50 = (n - fail50) / n if n else 0.0
    cat = Counter(x['category'] for x in detailed)

    base_r50 = None
    try:
        base_r50 = float(report['before']['semantic_recall']['recall_at_50']['rate'])
    except Exception:
        pass
    after_r50 = None
    try:
        after_r50 = float(report['after']['semantic_recall']['recall_at_50']['rate'])
    except Exception:
        after_r50 = inferred_r50

    max_if_index_fixed = min(1.0, after_r50 + cat.get('INDEX_OR_CHUNK_REPRESENTATION', 0) / n)
    summary = {
        'status': 'RETRIEVAL_RESIDUAL_FAILURE_REVIEW_COMPLETE',
        'retrieval_gate_passed': False,
        'reranker_stage_blocked': True,
        'stage_b_blocked': True,
        'plab36_adjudication_blocked': True,
        'final_independent_test_blocked': True,
        'n_queries': n,
        'residual_failure_n': fail50,
        'inferred_semantic_recall_at_50': round(inferred_r50, 4),
        'reported_semantic_recall_at_50': round(after_r50, 4) if after_r50 is not None else None,
        'baseline_semantic_recall_at_50': round(base_r50, 4) if base_r50 is not None else None,
        'delta_vs_baseline_at_50': round(after_r50 - base_r50, 4) if after_r50 is not None and base_r50 is not None else None,
        'category_counts': dict(cat),
        'max_semantic_recall_at_50_if_all_index_chunk_failures_fixed': round(max_if_index_fixed, 4),
        'next_scientific_state': 'RETRIEVAL_RESIDUAL_FAILURE_REVIEW_COMPLETE_NO_RERANKER',
        'notes': [
            'No model weights were loaded and no benchmark was rerun by this review.',
            'This review does not authorize a second adaptation run.',
            'Reranker remains blocked until retrieval development gate passes.',
        ],
    }

    out_root = root_path(cfg['outputs']['root'])
    json_path = out_root / 'residual_review.json'
    md_path = out_root / 'residual_review.md'
    atomic_json(json_path, {'summary': summary, 'failures': detailed})

    lines = [
        '# Qwen4B Retrieval Residual Failure Review', '',
        f"- Gate: **FAILED**",
        f"- Queries: {n}",
        f"- Residual failures outside Top-50: {fail50}",
        f"- Semantic Recall@50: {after_r50:.1%}",
    ]
    if base_r50 is not None:
        lines.append(f"- Baseline Semantic Recall@50: {base_r50:.1%}")
        lines.append(f"- Delta vs baseline: {(after_r50-base_r50):+.1%}")
    lines += [
        f"- If every index/chunk failure were fixed: max Recall@50 = {max_if_index_fixed:.1%}",
        '', '## Failure taxonomy', ''
    ]
    for k, v in sorted(cat.items()):
        lines.append(f"- {k}: {v}")
    lines += ['', '## Scientific decision', '',
              '- Do not advance to reranker.',
              '- Do not run Stage-B, PLAB36 adjudication, or final independent test.',
              '- Do not reinterpret this report as permission for a second adaptation run.',
              '- Preserve the current adapter and reports as the bounded adaptation result.',
              '']
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    main(load_config(args.config))
