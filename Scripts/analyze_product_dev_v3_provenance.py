from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

from qwen4b_adaptation_common import load_config, root_path, atomic_json, verify_product_dev_sha


def main(cfg):
    product_sha = verify_product_dev_sha(cfg)
    items = json.loads(root_path(cfg['data']['product_dev_v3']).read_text(encoding='utf-8'))
    audit_path = root_path(cfg['outputs']['root']) / 'product_dev_v3_qrel_integrity_audit.json'
    if not audit_path.exists():
        raise RuntimeError('QREL_INTEGRITY_AUDIT_NOT_FOUND')
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    if audit.get('summary', {}).get('benchmark_sha256') != product_sha:
        raise RuntimeError('AUDIT_BENCHMARK_SHA_MISMATCH')

    audit_rows = {str(x['query_id']): x for x in audit.get('items', [])}
    by_provenance = defaultdict(lambda: {
        'n_items': 0,
        'query_ids': [],
        'hard_integrity_n': 0,
        'hard_integrity_query_ids': [],
        'provenance_alignment_n': 0,
        'provenance_alignment_query_ids': [],
        'heuristic_review_n': 0,
        'heuristic_review_query_ids': [],
    })

    for it in items:
        qid = str(it.get('query_id'))
        prov = str(it.get('provenance') or 'UNSPECIFIED')
        row = audit_rows.get(qid)
        if row is None:
            raise RuntimeError(f'AUDIT_ROW_MISSING query_id={qid}')
        g = by_provenance[prov]
        g['n_items'] += 1
        g['query_ids'].append(qid)
        if row.get('hard_integrity_flags'):
            g['hard_integrity_n'] += 1
            g['hard_integrity_query_ids'].append(qid)
        if row.get('provenance_alignment_flags'):
            g['provenance_alignment_n'] += 1
            g['provenance_alignment_query_ids'].append(qid)
        if row.get('heuristic_review_flags'):
            g['heuristic_review_n'] += 1
            g['heuristic_review_query_ids'].append(qid)

    matrix = {}
    for prov, g in sorted(by_provenance.items()):
        n = g['n_items']
        matrix[prov] = {
            **g,
            'hard_integrity_rate': round(g['hard_integrity_n'] / n, 4) if n else 0.0,
            'provenance_alignment_rate': round(g['provenance_alignment_n'] / n, 4) if n else 0.0,
            'heuristic_review_rate': round(g['heuristic_review_n'] / n, 4) if n else 0.0,
        }

    synthetic_labels = {'BLUEPRINT_EXPANSION_SPEC', 'BLUEPRINT_TARGETED_FILL'}
    synthetic_n = sum(v['n_items'] for k, v in matrix.items() if k in synthetic_labels)
    synthetic_alignment_n = sum(v['provenance_alignment_n'] for k, v in matrix.items() if k in synthetic_labels)
    synthetic_hard_n = sum(v['hard_integrity_n'] for k, v in matrix.items() if k in synthetic_labels)
    non_synthetic_n = len(items) - synthetic_n
    non_synthetic_alignment_n = sum(v['provenance_alignment_n'] for k, v in matrix.items() if k not in synthetic_labels)

    systematic = bool(
        synthetic_n > 0
        and synthetic_alignment_n == synthetic_n
        and non_synthetic_alignment_n == 0
    )
    gate_authority = 'SUSPENDED_PENDING_SOURCE_GROUNDED_RECONSTRUCTION' if systematic or synthetic_hard_n else 'UNCHANGED'

    summary = {
        'status': 'PRODUCT_DEV_V3_PROVENANCE_ANALYSIS_COMPLETE',
        'benchmark_sha256': product_sha,
        'n_items': len(items),
        'synthetic_provenance_labels': sorted(synthetic_labels),
        'synthetic_item_n': synthetic_n,
        'synthetic_provenance_alignment_n': synthetic_alignment_n,
        'synthetic_hard_integrity_n': synthetic_hard_n,
        'non_synthetic_item_n': non_synthetic_n,
        'non_synthetic_provenance_alignment_n': non_synthetic_alignment_n,
        'systematic_synthetic_construction_defect': systematic,
        'retrieval_gate_authority': gate_authority,
        'benchmark_mutated': False,
        'model_weights_loaded': False,
        'benchmark_rerun': False,
        'second_adaptation_authorized': False,
        'reranker_authorized': False,
        'decision': (
            'Do not interpret PRODUCT_DEV_V3 retrieval gate as authoritative until flagged synthetic items are '
            'reconstructed from the frozen corpus with source-grounded qrels and independently adjudicated.'
            if gate_authority != 'UNCHANGED' else
            'No provenance-specific systematic construction defect was established by this analysis.'
        ),
    }

    out_root = root_path(cfg['outputs']['root'])
    atomic_json(out_root / 'product_dev_v3_provenance_analysis.json', {'summary': summary, 'provenance_matrix': matrix})

    lines = [
        '# PRODUCT_DEV_V3 Provenance Analysis', '',
        f"- Benchmark SHA256: `{product_sha}`",
        f"- Items: {len(items)}",
        f"- Synthetic items: {synthetic_n}",
        f"- Synthetic provenance-alignment failures: {synthetic_alignment_n}",
        f"- Synthetic hard-integrity failures: {synthetic_hard_n}",
        f"- Non-synthetic provenance-alignment failures: {non_synthetic_alignment_n}",
        f"- Systematic synthetic construction defect: **{systematic}**",
        f"- Retrieval-gate authority: **{gate_authority}**", '',
        '## Provenance matrix', ''
    ]
    for prov, g in matrix.items():
        lines += [
            f"### {prov}",
            f"- n: {g['n_items']}",
            f"- hard integrity: {g['hard_integrity_n']} ({g['hard_integrity_rate']:.1%})",
            f"- provenance alignment: {g['provenance_alignment_n']} ({g['provenance_alignment_rate']:.1%})",
            f"- heuristic review: {g['heuristic_review_n']} ({g['heuristic_review_rate']:.1%})", ''
        ]
    lines += [
        '## Scientific decision', '',
        '- Preserve the completed bounded adaptation and its artifacts unchanged.',
        '- Do not run a second adaptation on the basis of this benchmark defect.',
        '- Do not advance to reranker or downstream gates.',
        '- Reconstruct only defective synthetic benchmark items from the frozen corpus using source-grounded qrels.',
        '- Keep reviewer adjudication blinded to model outcomes.',
        ''
    ]
    (out_root / 'product_dev_v3_provenance_analysis.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    main(load_config(args.config))
