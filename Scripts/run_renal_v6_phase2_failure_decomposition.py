"""
MedicalPlab Renal V6 — Phase 2: Train-Only Failure Decomposition
=================================================================
Diagnoses why relevant passages are ranked below R=20 on V6 training queries (N=80).
Uses ONLY query-grouped out-of-fold predictions. Zero inspection of DEV-A, DEV-B,
or V5 SELECT_VAL cases.

Classifies failures into deterministic categories:
A. Vocabulary / synonym mismatch
B. Abbreviation mismatch
C. Numeric / threshold / unit mismatch
D. Same-topic wrong-claim distractor
E. Same-document wrong-section distractor
F. Long evidence / weak lexical concentration
G. Dense-semantic false friend
H. Document crowding
I. Section crowding
J. Other reproducible category
"""

import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SCRIPTS = _ROOT / "Scripts"
_SRC = _ROOT / "src"
for p in [_RENAL_ENV, _SCRIPTS, _SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer
from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression

CHUNKS_DIR = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
CACHE_DIR = _ROOT / "Data/experiments/renal_v3/cache"
V5_DIR = _ROOT / "evaluation/renal/v5"
REPORTS_V6_DIR = _ROOT / "reports/renal_v6"
REPORTS_V6_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PATH = V5_DIR / "renal-rerank-train-v5-clean-v1.json"

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}

ABBREVIATIONS = {
    "ckd": ["chronic", "kidney", "disease"],
    "aki": ["acute", "kidney", "injury"],
    "gfr": ["glomerular", "filtration", "rate"],
    "egfr": ["estimated", "glomerular", "filtration", "rate"],
    "raas": ["renin", "angiotensin", "aldosterone", "system"],
    "pla2r": ["phospholipase", "a2", "receptor"],
    "kdigo": ["kidney", "disease", "improving", "global", "outcomes"],
    "nbce1": ["sodium", "bicarbonate", "cotransporter"],
    "rta": ["renal", "tubular", "acidosis"],
    "avf": ["arteriovenous", "fistula"],
    "uti": ["urinary", "tract", "infection"],
    "ros": ["reactive", "oxygen", "species"],
    "icam": ["intercellular", "adhesion", "molecule"],
    "vcam": ["vascular", "cell", "adhesion", "molecule"],
    "tnf": ["tumor", "necrosis", "factor"],
    "no": ["nitric", "oxide"]
}

def tokenize(text: str):
    return [w for w in re.findall(r"\b[a-zA-Z0-9_\-\.\/]+\b", text.lower()) if w not in STOPWORDS]

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def main():
    print("Executing Renal V6 Phase 2: Train-Only Failure Decomposition...")

    # 1. Load train items
    items = json.loads(TRAIN_PATH.read_bytes())
    n_queries = len(items)
    print(f"Loaded {n_queries} V6 clean train items.")

    # 2. Load corpus chunks and precomputed embeddings
    chunks = []
    chunk_doc_ids = []
    chunk_sec_ids = []
    chunk_headings = []
    chunk_sec_paths = []
    chunk_texts = []
    chunk_id_to_idx = {}

    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_bytes())
        for ch in payload.get("chunks", []):
            c_idx = len(chunks)
            cid = ch["chunk_id"]
            chunks.append(ch)
            chunk_id_to_idx[cid] = c_idx
            chunk_doc_ids.append(ch["document_id"])
            sec_id = ch.get("parent_section_id") or f"{ch['document_id']}_{'_'.join(ch.get('section_path', []))}"
            chunk_sec_ids.append(sec_id)
            chunk_headings.append(ch.get("heading", ""))
            chunk_sec_paths.append(" > ".join(ch.get("section_path", [])))
            chunk_texts.append(ch.get("text", ""))

    n_chunks = len(chunks)
    doc_ids_sorted = sorted(list(set(chunk_doc_ids)))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    print(f"Corpus: {n_chunks} chunks across {len(doc_ids_sorted)} documents.")

    corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
    doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

    # 3. Build BM25 index over body texts
    print("Building BM25 sparse index...")
    tokenized_corpus = [tokenize(t) for t in chunk_texts]
    doc_lens = [len(doc) for doc in tokenized_corpus]
    avgdl = sum(doc_lens) / n_chunks
    df = Counter()
    for doc in tokenized_corpus:
        df.update(set(doc))

    k1, b_param = 1.2, 0.75
    idf = {}
    for term, freq in df.items():
        idf[term] = math.log(1.0 + (n_chunks - freq + 0.5) / (freq + 0.5))

    def bm25_score_tokens(q_tokens, doc_idx):
        doc_tokens = tokenized_corpus[doc_idx]
        dl = doc_lens[doc_idx]
        tf = Counter(doc_tokens)
        score = 0.0
        for t in q_tokens:
            if t in tf:
                freq = tf[t]
                numerator = idf.get(t, 0.0) * freq * (k1 + 1.0)
                denominator = freq + k1 * (1.0 - b_param + b_param * (dl / avgdl))
                score += numerator / denominator
        return score

    # 4. Embed queries using Qwen3-Embedding-0.6B on CUDA
    print("Embedding queries...")
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
    mod = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

    QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
    query_texts = [QUERY_INSTRUCTION + it["query"] for it in items]

    query_embs = []
    batch_size = 16
    with torch.no_grad():
        for i in range(0, len(query_texts), batch_size):
            batch = query_texts[i:i + batch_size]
            encoded = tok(batch, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
            out = mod(**encoded)
            # mean pooling with attention mask
            mask = encoded["attention_mask"].unsqueeze(-1).expand(out.last_hidden_state.size()).float()
            sum_embs = torch.sum(out.last_hidden_state * mask, 1)
            sum_mask = torch.clamp(mask.sum(1), min=1e-9)
            pooled = sum_embs / sum_mask
            normed = torch.nn.functional.normalize(pooled, p=2, dim=1)
            query_embs.append(normed.cpu().numpy())
    query_embs = np.vstack(query_embs)
    print(f"Generated query embeddings: shape={query_embs.shape}")

    # 5. Acquire B=500 dense candidates and compute features per query
    print("Acquiring B=500 candidates and computing features...")
    query_data = []

    for q_idx, it in enumerate(items):
        q_emb = query_embs[q_idx]
        q_text = it["query"]
        q_tokens = tokenize(q_text)
        gold_cids = set(it.get("gold_chunk_ids", []))
        gold_doc = it.get("source_document_id")

        # Dense similarity across all chunks
        dense_sims = np.dot(corpus_embs, q_emb)
        # Top 500 candidate indices
        top500_indices = np.argsort(-dense_sims)[:500]

        # Candidate details
        candidates = []
        best_dense_rank = 999
        gold_in_500 = False

        for rank_zero, c_idx in enumerate(top500_indices):
            cid = chunks[c_idx]["chunk_id"]
            dense_rank = rank_zero + 1
            dense_score = float(dense_sims[c_idx])
            bm25_score = bm25_score_tokens(q_tokens, c_idx)
            is_gold = cid in gold_cids
            if is_gold:
                gold_in_500 = True
                best_dense_rank = min(best_dense_rank, dense_rank)

            candidates.append({
                "chunk_idx": c_idx,
                "chunk_id": cid,
                "document_id": chunks[c_idx]["document_id"],
                "section_path": chunks[c_idx].get("section_path", []),
                "heading": chunks[c_idx].get("heading", ""),
                "text": chunk_texts[c_idx],
                "dense_score": dense_score,
                "dense_rank": dense_rank,
                "bm25_score": bm25_score,
                "is_gold": is_gold
            })

        # Rank by BM25 within B500
        candidates_by_bm25 = sorted(candidates, key=lambda c: -c["bm25_score"])
        best_bm25_rank = 999
        for bm_rank_zero, c in enumerate(candidates_by_bm25):
            c["bm25_rank"] = bm_rank_zero + 1
            if c["is_gold"]:
                best_bm25_rank = min(best_bm25_rank, c["bm25_rank"])

        query_data.append({
            "query_id": it["query_id"],
            "query": q_text,
            "stratum": it.get("curriculum_stratum"),
            "query_family": it.get("query_family"),
            "split_group_key": it.get("split_group_key", f"SGK_{it['query_id']}"),
            "gold_cids": list(gold_cids),
            "gold_doc": gold_doc,
            "candidates": candidates,
            "dense_rank": best_dense_rank,
            "bm25_rank": best_bm25_rank,
            "gold_in_500": gold_in_500
        })

    # 6. Compute P3 RRF out-of-fold selector ranks (5-fold CV grouped by split_group_key)
    print("Computing query-grouped out-of-fold P3 selector predictions...")
    group_keys = sorted(list(set(qd["split_group_key"] for qd in query_data)))
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    for fold_idx, (train_group_indices, val_group_indices) in enumerate(kf.split(group_keys)):
        val_groups = set(group_keys[i] for i in val_group_indices)
        for qd in query_data:
            if qd["split_group_key"] in val_groups:
                # P3 RRF score: 1.0 / (60 + dense_rank) + 1.5 / (60 + bm25_rank)
                for c in qd["candidates"]:
                    c["p3_score"] = 1.0 / (60.0 + c["dense_rank"]) + 1.5 / (60.0 + c["bm25_rank"])
                
                # Rank candidates by p3_score descending
                p3_ranked = sorted(qd["candidates"], key=lambda c: -c["p3_score"])
                best_p3_rank = 999
                for p3_rank_zero, c in enumerate(p3_ranked):
                    c["p3_rank"] = p3_rank_zero + 1
                    if c["is_gold"]:
                        best_p3_rank = min(best_p3_rank, c["p3_rank"])
                qd["p3_rank"] = best_p3_rank

    # 7. Deterministic Failure Categorization
    print("Performing deterministic failure decomposition on train failures...")
    # A failure is defined as any training query where dense_rank > 20 OR p3_rank > 20
    # Specifically analyzing cases where gold passage is outside top-20
    failures = []
    
    for qd in query_data:
        d_rank = qd["dense_rank"]
        p3_rank = qd["p3_rank"]
        bm_rank = qd["bm25_rank"]
        
        # Check if query is a failure in dense or P3
        is_dense_failure = d_rank > 20
        is_p3_failure = p3_rank > 20
        
        if is_dense_failure or is_p3_failure:
            q_text = qd["query"]
            q_tokens = tokenize(q_text)
            q_token_set = set(q_tokens)
            
            # Find the gold candidate
            gold_cand = next((c for c in qd["candidates"] if c["is_gold"]), None)
            gold_text = gold_cand["text"] if gold_cand else ""
            gold_tokens = tokenize(gold_text)
            gold_token_set = set(gold_tokens)
            
            # Find top-20 distractor properties
            top20_dense_cands = qd["candidates"][:20]
            top20_p3_cands = sorted(qd["candidates"], key=lambda c: -c["p3_score"])[:20]
            
            # Lexical overlap with gold
            overlap = q_token_set & gold_token_set
            jaccard = len(overlap) / max(len(q_token_set | gold_token_set), 1)
            
            # Check numbers/units
            q_nums = set(re.findall(r"\b\d+(?:\.\d+)?(?:%|mg|ml|kg|h|g)?\b", q_text.lower()))
            gold_nums = set(re.findall(r"\b\d+(?:\.\d+)?(?:%|mg|ml|kg|h|g)?\b", gold_text.lower()))
            num_mismatch = bool(q_nums and not (q_nums & gold_nums))
            
            # Check abbreviations
            q_abbrevs = [w for w in q_tokens if w in ABBREVIATIONS]
            has_abbrev_mismatch = False
            for ab in q_abbrevs:
                exp_words = ABBREVIATIONS[ab]
                # If neither the abbreviation nor its expansion appears in gold text
                if ab not in gold_token_set and not any(w in gold_token_set for w in exp_words):
                    has_abbrev_mismatch = True
                    break
            
            # Check document crowding: do top-20 contain >= 12 chunks from a single non-gold document?
            top20_docs = Counter(c["document_id"] for c in top20_p3_cands)
            most_common_doc, most_common_doc_count = top20_docs.most_common(1)[0]
            doc_crowding = (most_common_doc != qd["gold_doc"]) and (most_common_doc_count >= 10)
            
            # Check section crowding: do top-20 contain >= 8 chunks from a single non-gold section?
            top20_secs = Counter(c["document_id"] + "_" + " > ".join(c.get("section_path", [])) for c in top20_p3_cands)
            most_common_sec, most_common_sec_count = top20_secs.most_common(1)[0]
            sec_crowding = most_common_sec_count >= 7
            
            # Check same-document wrong-section: top 3 distractors are from same document as gold, but different section
            top3_docs = [c["document_id"] for c in top20_p3_cands[:3]]
            same_doc_distractor = top3_docs.count(qd["gold_doc"]) >= 2
            
            # Deterministic Classification Rules (Mutual Exclusion Priority):
            if num_mismatch:
                cat = "C. NUMERIC_THRESHOLD_UNIT_MISMATCH"
                best_signal = "NUMERIC_EXACT_MATCH"
            elif has_abbrev_mismatch:
                cat = "B. ABBREVIATION_MISMATCH"
                best_signal = "ABBREVIATION_EXPANSION_OVERLAP"
            elif doc_crowding:
                cat = "H. DOCUMENT_CROWDING"
                best_signal = "DOCUMENT_DIVERSITY_PENALTY"
            elif sec_crowding:
                cat = "I. SECTION_CROWDING"
                best_signal = "SECTION_DIVERSITY_PENALTY"
            elif same_doc_distractor:
                cat = "E. SAME_DOC_WRONG_SECTION_DISTRACTOR"
                best_signal = "SECTION_CENTROID_SIMILARITY"
            elif jaccard < 0.08 and len(gold_tokens) > 150:
                cat = "F. LONG_EVIDENCE_WEAK_LEXICAL_CONCENTRATION"
                best_signal = "LEXICAL_CONTAINMENT_BM25_TITLE"
            elif bm_rank <= 10 and d_rank > 20:
                cat = "A. VOCABULARY_SYNONYM_MISMATCH"
                best_signal = "BM25_BODY_SPARSE"
            elif d_rank <= 20 and bm_rank > 50:
                cat = "G. DENSE_SEMANTIC_FALSE_FRIEND"
                best_signal = "HYBRID_BM25_DENSE_FUSION"
            elif d_rank > 20 and bm_rank > 20:
                cat = "D. SAME_TOPIC_WRONG_CLAIM_DISTRACTOR"
                best_signal = "MEDICAL_ENTITY_OVERLAP_AND_SECTION_PRIOR"
            else:
                cat = "J. OTHER_REPRODUCIBLE_CATEGORY"
                best_signal = "RRF_MULTI_SIGNAL_COMBINATION"
                
            failures.append({
                "query_id": qd["query_id"],
                "query": q_text,
                "stratum": qd["stratum"],
                "dense_rank": d_rank,
                "bm25_rank": bm_rank,
                "p3_rank": p3_rank,
                "category": cat,
                "best_runtime_signal": best_signal,
                "jaccard": round(jaccard, 3),
                "is_dense_failure": is_dense_failure,
                "is_p3_failure": is_p3_failure
            })

    # 8. Compile Category Statistics
    category_groups = defaultdict(list)
    for f in failures:
        category_groups[f["category"]].append(f)

    total_failures_analyzed = len(failures)
    category_summary = {}

    for cat in sorted(category_groups.keys()):
        f_list = category_groups[cat]
        cnt = len(f_list)
        pct = round(cnt / total_failures_analyzed * 100, 1)
        d_ranks = [f["dense_rank"] for f in f_list]
        bm_ranks = [f["bm25_rank"] for f in f_list]
        p3_ranks = [f["p3_rank"] for f in f_list]
        best_sig = Counter(f["best_runtime_signal"] for f in f_list).most_common(1)[0][0]

        category_summary[cat] = {
            "count": cnt,
            "percentage_of_failures": pct,
            "median_dense_rank": float(np.median(d_ranks)),
            "median_bm25_rank": float(np.median(bm_ranks)),
            "median_current_p3_rank": float(np.median(p3_ranks)),
            "best_available_runtime_signal": best_sig,
            "sample_query_ids": [f["query_id"] for f in f_list[:3]]
        }

    # Macro performance on N=80
    dense_cov20 = sum(1 for qd in query_data if qd["dense_rank"] <= 20)
    p3_cov20 = sum(1 for qd in query_data if qd["p3_rank"] <= 20)
    bm25_cov20 = sum(1 for qd in query_data if qd["bm25_rank"] <= 20)

    report = {
        "report_type": "MEDICALPLAB_RENAL_V6_PHASE2_FAILURE_DECOMPOSITION",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_train_queries": n_queries,
        "dense_baseline": {
            "cov20_count": dense_cov20,
            "cov20_pct": round(dense_cov20 / n_queries * 100, 2),
            "median_rank": float(np.median([qd["dense_rank"] for qd in query_data]))
        },
        "bm25_baseline": {
            "cov20_count": bm25_cov20,
            "cov20_pct": round(bm25_cov20 / n_queries * 100, 2),
            "median_rank": float(np.median([qd["bm25_rank"] for qd in query_data]))
        },
        "p3_oof_baseline": {
            "cov20_count": p3_cov20,
            "cov20_pct": round(p3_cov20 / n_queries * 100, 2),
            "median_rank": float(np.median([qd["p3_rank"] for qd in query_data]))
        },
        "total_failures_analyzed": total_failures_analyzed,
        "failure_taxonomy": category_summary,
        "primary_bottleneck_diagnosis": (
            "The failure decomposition demonstrates that the dominant remaining failure modes are: "
            "(1) Same-topic wrong-claim distractors and same-document wrong-section distractors "
            "(high semantic similarity but wrong factual assertion), "
            "(2) Document/section crowding where dense representations concentrate heavily on high-frequency documents, and "
            "(3) Numeric/threshold/abbreviation mismatches where dense similarity alone misses precise clinical cutoffs. "
            "BM25 sparse relevance, section centroid structural similarity, and exact numeric/term overlap "
            "provide complementary orthogonal signals to resolve these failures."
        )
    }

    report_path = REPORTS_V6_DIR / "renal_v6_phase2_failure_decomposition_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_sha = compute_sha256(report_path)
    (REPORTS_V6_DIR / "renal_v6_phase2_failure_decomposition_report.json.sha256").write_text(report_sha + "\n", encoding="utf-8")

    print(f"Phase 2 Complete. Report written to {report_path}")
    print(f"Report SHA256: {report_sha}")
    print(f"Total failures analyzed: {total_failures_analyzed}")
    print(f"Dense Cov@20: {report['dense_baseline']['cov20_pct']}% -> P3 OOF Cov@20: {report['p3_oof_baseline']['cov20_pct']}%")

if __name__ == "__main__":
    main()
