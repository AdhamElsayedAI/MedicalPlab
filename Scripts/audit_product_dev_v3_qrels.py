from __future__ import annotations

import argparse
import csv
import json
from collections import Counter

from qwen4b_adaptation_common import (
    atomic_json,
    jaccard,
    load_chunks,
    load_config,
    normalize_text,
    resolve_corpus_dir,
    root_path,
    token_set,
    verify_product_dev_sha,
)

STOPWORDS = {
    'the','a','an','and','or','of','to','in','on','for','with','by','from','as','at','is','are','was','were','be','been',
    'being','what','which','how','why','when','where','who','does','do','did','can','could','should','would','may','might',
    'this','that','these','those','into','than','their','its','via','between','regarding','during','after','before','through',
    'patient','patients','disease','clinical','effect','effects','role','system','treatment','therapy','mechanism','cause','causes',
}


def meaningful_tokens(text: str) -> set[str]:
    return {t for t in token_set(text or '') if len(t) >= 3 and t not in STOPWORDS}


def token_recall(source: str, target: str) -> float:
    s = meaningful_tokens(source)
    t = meaningful_tokens(target)
    return len(s & t) / len(s) if s else 0.0


def span_matches_text(span: str, text: str) -> bool:
    a = normalize_text(span)
    b = normalize_text(text)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    return jaccard(a, b) >= 0.55


def best_same_document_match(chunks, ordered, document_id: str, probe: str):
    best = None
    for cid in ordered:
        ch = chunks[cid]
        if str(ch.get('document_id')) != str(document_id):
            continue
        score = jaccard(probe, ch.get('text', ''))
        if best is None or score > best['score']:
            best = {'chunk_id': cid, 'score': score, 'text_preview': ch.get('text', '')[:260]}
    return best


def _residual_map(cfg):
    path = root_path(cfg['outputs']['evaluation_report'])
    if not path.exists():
        return {}
    report = json.loads(path.read_text(encoding='utf-8'))
    return {str(r.get('query_id')): r for r in report.get('residual_failures', []) if r.get('query_id')}


def audit(cfg):
    product_sha = verify_product_dev_sha(cfg)
    items = json.loads(root_path(cfg['data']['product_dev_v3']).read_text(encoding='utf-8'))
    chunks, ordered = load_chunks(resolve_corpus_dir(cfg))
    residuals = _residual_map(cfg)

    rows = []
    hard_counts = Counter()
    provenance_counts = Counter()
    heuristic_counts = Counter()

    for it in items:
        qid = str(it.get('query_id'))
        query = str(it.get('query') or '')
        claim = str(it.get('canonical_claim') or '')
        evidence = str(it.get('evidence_span') or '')
        gold_doc = str(it.get('gold_document_id') or '')
        exact = [str(x) for x in it.get('exact_gold_chunk_ids', [])]
        support = [str(x) for x in it.get('semantic_support_chunk_ids', exact)]

        hard = []
        provenance = []
        heuristic = []

        missing_exact = [cid for cid in exact if cid not in chunks]
        missing_support = [cid for cid in support if cid not in chunks]
        if missing_exact:
            hard.append('MISSING_EXACT_GOLD_CHUNK')
        if missing_support:
            hard.append('MISSING_SEMANTIC_SUPPORT_CHUNK')

        present_support = [chunks[cid] for cid in support if cid in chunks]
        doc_mismatch_ids = [
            cid for cid in support if cid in chunks and str(chunks[cid].get('document_id')) != gold_doc
        ]
        if doc_mismatch_ids:
            hard.append('GOLD_DOCUMENT_ID_MISMATCH')

        support_text = '\n'.join(ch.get('text', '') for ch in present_support)
        span_in_support = any(span_matches_text(evidence, ch.get('text', '')) for ch in present_support) if evidence else False
        if evidence and not span_in_support:
            provenance.append('EVIDENCE_SPAN_NOT_ALIGNED_TO_SUPPORT_CHUNKS')

        q_support = token_recall(query, support_text)
        c_support = token_recall(claim, support_text)
        q_evidence = token_recall(query, evidence)
        c_evidence = token_recall(claim, evidence)

        if q_support < 0.15 and c_support < 0.15:
            heuristic.append('LOW_QUERY_CLAIM_TO_SUPPORT_LEXICAL_ALIGNMENT')
        if evidence and q_evidence < 0.15 and c_evidence < 0.15:
            heuristic.append('LOW_QUERY_CLAIM_TO_EVIDENCE_LEXICAL_ALIGNMENT')

        labeled_scores = [jaccard(claim or query, chunks[cid].get('text', '')) for cid in support if cid in chunks]
        best_labeled = max(labeled_scores) if labeled_scores else 0.0
        best_doc = best_same_document_match(chunks, ordered, gold_doc, claim or query) if gold_doc else None
        if best_doc and best_doc['score'] >= 0.15 and best_doc['score'] > best_labeled + 0.08:
            heuristic.append('BETTER_SAME_DOCUMENT_LEXICAL_MATCH_THAN_LABELED_SUPPORT')

        for x in hard: hard_counts[x] += 1
        for x in provenance: provenance_counts[x] += 1
        for x in heuristic: heuristic_counts[x] += 1

        residual = residuals.get(qid, {})
        if hard:
            priority = 'P0_HARD_INTEGRITY'
        elif provenance:
            priority = 'P1_PROVENANCE_ALIGNMENT'
        elif heuristic:
            priority = 'P2_HEURISTIC_REVIEW'
        else:
            priority = None

        rows.append({
            'query_id': qid,
            'query': query,
            'canonical_claim': claim,
            'gold_document_id': gold_doc,
            'exact_gold_chunk_ids': exact,
            'semantic_support_chunk_ids': support,
            'missing_exact_gold_chunk_ids': missing_exact,
            'missing_semantic_support_chunk_ids': missing_support,
            'document_mismatch_chunk_ids': doc_mismatch_ids,
            'evidence_span': evidence,
            'evidence_span_aligned_to_support_chunks': span_in_support,
            'query_to_support_token_recall': round(q_support, 4),
            'claim_to_support_token_recall': round(c_support, 4),
            'query_to_evidence_token_recall': round(q_evidence, 4),
            'claim_to_evidence_token_recall': round(c_evidence, 4),
            'best_labeled_support_claim_jaccard': round(best_labeled, 4),
            'best_same_document_claim_match': ({
                'chunk_id': best_doc['chunk_id'],
                'score': round(best_doc['score'], 4),
                'text_preview': best_doc['text_preview'],
            } if best_doc else None),
            'support_previews': [
                {
                    'chunk_id': cid,
                    'document_id': chunks[cid].get('document_id'),
                    'section_path': chunks[cid].get('section_path'),
                    'text_preview': chunks[cid].get('text', '')[:320],
                }
                for cid in support if cid in chunks
            ],
            'hard_integrity_flags': hard,
            'provenance_alignment_flags': provenance,
            'heuristic_review_flags': heuristic,
            'manual_review_priority': priority,
            'retrieval_residual_rank': residual.get('rank'),
            'retrieval_residual_category': residual.get('category'),
            'outside_top_50_after_adaptation': qid in residuals,
        })

    hard_flagged = [r for r in rows if r['hard_integrity_flags']]
    provenance_flagged = [r for r in rows if r['provenance_alignment_flags']]
    heuristic_flagged = [r for r in rows if r['heuristic_review_flags']]
    queue = [r for r in rows if r['manual_review_priority']]
    priority_order = {'P0_HARD_INTEGRITY': 0, 'P1_PROVENANCE_ALIGNMENT': 1, 'P2_HEURISTIC_REVIEW': 2}
    queue.sort(key=lambda r: (priority_order[r['manual_review_priority']], not r['outside_top_50_after_adaptation'], r['query_id']))

    score_state = 'PROVISIONAL_PENDING_QREL_ADJUDICATION' if (hard_flagged or provenance_flagged) else 'BENCHMARK_INTEGRITY_CHECK_PASSED'
    summary = {
        'status': 'PRODUCT_DEV_V3_QREL_INTEGRITY_AUDIT_COMPLETE',
        'benchmark_sha256': product_sha,
        'n_items': len(items),
        'hard_integrity_flagged_n': len(hard_flagged),
        'provenance_alignment_flagged_n': len(provenance_flagged),
        'heuristic_review_flagged_n': len(heuristic_flagged),
        'manual_review_queue_n': len(queue),
        'hard_integrity_flag_counts': dict(sorted(hard_counts.items())),
        'provenance_alignment_flag_counts': dict(sorted(provenance_counts.items())),
        'heuristic_review_flag_counts': dict(sorted(heuristic_counts.items())),
        'score_interpretation': score_state,
        'benchmark_mutated': False,
        'model_weights_loaded': False,
        'benchmark_rerun': False,
        'interpretation': (
            'Hard integrity flags are deterministic missing-ID or document-consistency defects. '
            'Provenance-alignment flags require human adjudication because a non-matching evidence span may reflect truncation, paraphrase, or an incorrect qrel. '
            'Heuristic flags are triage only and are never automatic invalidation.'
        ),
    }

    out_root = root_path(cfg['outputs']['root'])
    atomic_json(out_root / 'product_dev_v3_qrel_integrity_audit.json', {'summary': summary, 'items': rows})
    atomic_json(out_root / 'product_dev_v3_qrel_review_queue.json', {'summary': summary, 'review_queue': queue})

    csv_path = out_root / 'product_dev_v3_qrel_review_queue.csv'
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open('w', encoding='utf-8-sig', newline='') as f:
        fields = [
            'manual_review_priority','query_id','outside_top_50_after_adaptation','retrieval_residual_rank',
            'query','canonical_claim','gold_document_id','exact_gold_chunk_ids','semantic_support_chunk_ids',
            'missing_exact_gold_chunk_ids','missing_semantic_support_chunk_ids','document_mismatch_chunk_ids',
            'evidence_span','hard_integrity_flags','provenance_alignment_flags','heuristic_review_flags',
            'best_same_document_chunk_id','best_same_document_score','review_decision','reviewer','review_notes'
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in queue:
            best = r.get('best_same_document_claim_match') or {}
            w.writerow({
                'manual_review_priority': r['manual_review_priority'],
                'query_id': r['query_id'],
                'outside_top_50_after_adaptation': r['outside_top_50_after_adaptation'],
                'retrieval_residual_rank': r['retrieval_residual_rank'],
                'query': r['query'],
                'canonical_claim': r['canonical_claim'],
                'gold_document_id': r['gold_document_id'],
                'exact_gold_chunk_ids': ';'.join(r['exact_gold_chunk_ids']),
                'semantic_support_chunk_ids': ';'.join(r['semantic_support_chunk_ids']),
                'missing_exact_gold_chunk_ids': ';'.join(r['missing_exact_gold_chunk_ids']),
                'missing_semantic_support_chunk_ids': ';'.join(r['missing_semantic_support_chunk_ids']),
                'document_mismatch_chunk_ids': ';'.join(r['document_mismatch_chunk_ids']),
                'evidence_span': r['evidence_span'],
                'hard_integrity_flags': ';'.join(r['hard_integrity_flags']),
                'provenance_alignment_flags': ';'.join(r['provenance_alignment_flags']),
                'heuristic_review_flags': ';'.join(r['heuristic_review_flags']),
                'best_same_document_chunk_id': best.get('chunk_id'),
                'best_same_document_score': best.get('score'),
                'review_decision': '',
                'reviewer': '',
                'review_notes': '',
            })

    md = [
        '# PRODUCT_DEV_V3 Qrel Integrity Audit', '',
        f"- SHA256: `{product_sha}`",
        f"- Items: {len(items)}",
        f"- Hard-integrity flagged: {len(hard_flagged)}",
        f"- Provenance-alignment flagged: {len(provenance_flagged)}",
        f"- Heuristic-review flagged: {len(heuristic_flagged)}",
        f"- Manual-review queue: {len(queue)}",
        f"- Score interpretation: **{score_state}**",
        '- Benchmark mutated: **No**',
        '- Model weights loaded: **No**',
        '- Benchmark rerun: **No**', '',
        '## Hard integrity flags', ''
    ]
    if hard_counts:
        md.extend(f'- {k}: {v}' for k, v in sorted(hard_counts.items()))
    else:
        md.append('- None')
    md += ['', '## Provenance-alignment flags', '']
    if provenance_counts:
        md.extend(f'- {k}: {v}' for k, v in sorted(provenance_counts.items()))
    else:
        md.append('- None')
    md += ['', '## Heuristic manual-review flags', '']
    if heuristic_counts:
        md.extend(f'- {k}: {v}' for k, v in sorted(heuristic_counts.items()))
    else:
        md.append('- None')
    md += [
        '', '## Scientific interpretation', '',
        '- Missing qrel chunk IDs and document-ID inconsistencies are hard integrity defects.',
        '- Evidence-span alignment failures require manual adjudication; they are not automatically invalid qrels.',
        '- Lexical heuristics are triage only; they do not authorize relabeling.',
        '- Do not use PRODUCT_DEV_V3 items for training.',
        '- Do not rerun adaptation or advance to reranker until benchmark adjudication is complete and retrieval gate validity is restored.',
        ''
    ]
    (out_root / 'product_dev_v3_qrel_integrity_audit.md').write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    audit(load_config(args.config))


if __name__ == '__main__':
    main()
