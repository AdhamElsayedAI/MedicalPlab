"""
MedicalPlab Renal V6 — Phase 3: Feature Oracle V2 & Stability Audit
====================================================================
Evaluates runtime-available signals only using 5-fold query-grouped CV on N=80 clean train.
No gold features, no benchmark IDs, no LLM-generated features.

Mandatory features:
1. Dense passage score & rank
2. BM25 BODY score & rank
3. BM25 TITLE score & rank
4. BM25 SECTION-HEADING score & rank
5. Document score & rank
6. Section centroid similarity & rank
7. Lexical containment
8. Lexical Jaccard
9. Deterministic abbreviation expansion overlap
10. Deterministic medical-term overlap
11. Numeric overlap
12. Unit overlap
13. Cutoff/inequality overlap
14. Local redundancy / crowding statistics

Reports for each feature and bounded combination:
Coverage@20, Coverage@50, MRR, median gold rank, p75, p90,
fold-by-fold Coverage@20, mean, std, worst fold, latency (ms/query).
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
from sklearn.linear_model import LogisticRegression, Ridge

CHUNKS_DIR = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
CACHE_DIR = _ROOT / "Data/experiments/renal_v3/cache"
V5_DIR = _ROOT / "evaluation/renal/v5"
REG_PATH = _ROOT / "Data/metadata/renal_source_registry_v2.json"
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
    "ckd": "chronic kidney disease",
    "aki": "acute kidney injury",
    "gfr": "glomerular filtration rate",
    "egfr": "estimated glomerular filtration rate",
    "raas": "renin angiotensin aldosterone system",
    "pla2r": "phospholipase a2 receptor",
    "kdigo": "kidney disease improving global outcomes",
    "nbce1": "sodium bicarbonate cotransporter",
    "rta": "renal tubular acidosis",
    "avf": "arteriovenous fistula",
    "uti": "urinary tract infection",
    "ros": "reactive oxygen species",
    "icam": "intercellular adhesion molecule",
    "vcam": "vascular cell adhesion molecule",
    "tnf": "tumor necrosis factor",
    "no": "nitric oxide",
    "acei": "angiotensin converting enzyme inhibitor",
    "arb": "angiotensin receptor blocker"
}

MEDICAL_TERMS = {
    "glomerular", "glomerulus", "podocyte", "podocytes", "proteinuria", "albuminuria",
    "nephron", "tubular", "proximal", "distal", "bicarbonate", "potassium", "hyperkalemia",
    "hypokalemia", "acidosis", "alkalosis", "endothelium", "vascular", "hemodynamics",
    "creatinine", "oliguria", "anuria", "dialysis", "hemodialysis", "fistula",
    "stenosis", "thrombosis", "nephrolithiasis", "urolithiasis", "stone", "calculi",
    "microbiome", "commensal", "lactobacillus", "urothelium", "cystitis", "pyelonephritis"
}

UNITS = {"%", "mg/dl", "mg/g", "ml/min", "ml/min/1.73m2", "ml/kg/h", "meq/l", "mmol/l", "g/dl", "ug/ml"}
CUTOFF_TERMS = {">", "<", ">=", "<=", "greater", "less", "exceeding", "below", "above", "threshold", "cutoff", "stage"}

def tokenize(text: str):
    return [w for w in re.findall(r"\b[a-zA-Z0-9_\-\.\/]+\b", text.lower()) if w not in STOPWORDS]

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def main():
    print("Executing Renal V6 Phase 3: Feature Oracle V2 & Stability Audit...")

    # 1. Load train dataset
    items = json.loads(TRAIN_PATH.read_bytes())
    n_queries = len(items)
    print(f"Loaded {n_queries} clean train queries.")

    # 2. Load registry for document titles
    doc_titles = {}
    if REG_PATH.exists():
        reg = json.loads(REG_PATH.read_bytes())
        for d in reg.get("documents", []):
            doc_titles[d["document_id"]] = d.get("title", "")

    # 3. Load corpus chunks and metadata
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

    # 4. Load precomputed embeddings
    corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
    doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

    # 5. Precompute Section Centroids
    sec_ids_unique = sorted(list(set(chunk_sec_ids)))
    sec_id_to_idx = {sid: i for i, sid in enumerate(sec_ids_unique)}
    sec_chunk_indices = defaultdict(list)
    for c_idx, sid in enumerate(chunk_sec_ids):
        sec_chunk_indices[sid].append(c_idx)

    sec_centroids = np.zeros((len(sec_ids_unique), corpus_embs.shape[1]), dtype=np.float32)
    for sid, c_indices in sec_chunk_indices.items():
        s_idx = sec_id_to_idx[sid]
        centroid = corpus_embs[c_indices].mean(axis=0)
        sec_centroids[s_idx] = centroid / np.linalg.norm(centroid)

    # 6. Build BM25 sparse indices:
    # A) Body
    tokenized_body = [tokenize(t) for t in chunk_texts]
    body_lens = [len(doc) for doc in tokenized_body]
    avgdl_body = sum(body_lens) / n_chunks
    df_body = Counter()
    for doc in tokenized_body:
        df_body.update(set(doc))
    idf_body = {t: math.log(1.0 + (n_chunks - f + 0.5) / (f + 0.5)) for t, f in df_body.items()}

    # B) Section Heading
    tokenized_heading = [tokenize(h + " " + sp) for h, sp in zip(chunk_headings, chunk_sec_paths)]
    heading_lens = [len(h) for h in tokenized_heading]
    avgdl_heading = max(sum(heading_lens) / n_chunks, 1.0)
    df_heading = Counter()
    for doc in tokenized_heading:
        df_heading.update(set(doc))
    idf_heading = {t: math.log(1.0 + (n_chunks - f + 0.5) / (f + 0.5)) for t, f in df_heading.items()}

    # C) Document Title
    tokenized_title = [tokenize(doc_titles.get(did, "")) for did in chunk_doc_ids]
    title_lens = [len(t) for t in tokenized_title]
    avgdl_title = max(sum(title_lens) / n_chunks, 1.0)
    df_title = Counter()
    for doc in tokenized_title:
        df_title.update(set(doc))
    idf_title = {t: math.log(1.0 + (n_chunks - f + 0.5) / (f + 0.5)) for t, f in df_title.items()}

    def bm25_score_tokens(q_tokens, doc_idx, tokenized_col, doc_lens, avgdl, idf):
        doc_tokens = tokenized_col[doc_idx]
        dl = doc_lens[doc_idx]
        if dl == 0: return 0.0
        tf = Counter(doc_tokens)
        score = 0.0
        k1, b = 1.2, 0.75
        for t in q_tokens:
            if t in tf:
                freq = tf[t]
                num = idf.get(t, 0.0) * freq * (k1 + 1.0)
                denom = freq + k1 * (1.0 - b + b * (dl / avgdl))
                score += num / denom
        return score

    # 7. Embed queries on CUDA
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
            mask = encoded["attention_mask"].unsqueeze(-1).expand(out.last_hidden_state.size()).float()
            pooled = torch.sum(out.last_hidden_state * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)
            normed = torch.nn.functional.normalize(pooled, p=2, dim=1)
            query_embs.append(normed.cpu().numpy())
    query_embs = np.vstack(query_embs)

    # 8. Feature Extraction at B=500 per query
    print("Extracting full Feature Oracle V2 feature matrix at B=500...")
    queries_data = []

    for q_idx, it in enumerate(items):
        q_emb = query_embs[q_idx]
        q_text = it["query"]
        q_tokens = tokenize(q_text)
        q_token_set = set(q_tokens)
        gold_cids = set(it.get("gold_chunk_ids", []))

        # Numbers, units, cutoffs in query
        q_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", q_text.lower()))
        q_units = set(w for w in q_tokens if w in UNITS)
        q_cutoffs = set(w for w in q_tokens if w in CUTOFF_TERMS)
        q_med_terms = set(w for w in q_tokens if w in MEDICAL_TERMS)
        q_abbrevs = [w for w in q_tokens if w in ABBREVIATIONS]
        q_abbrev_expansions = []
        for ab in q_abbrevs:
            q_abbrev_expansions.extend(tokenize(ABBREVIATIONS[ab]))
        q_abbrev_exp_set = set(q_abbrev_expansions)

        # Dense similarity
        dense_sims = np.dot(corpus_embs, q_emb)
        top500_indices = np.argsort(-dense_sims)[:500]

        # Document similarities (23 docs)
        doc_sims = np.dot(doc_embs, q_emb)

        # Section centroid similarities
        sec_sims = np.dot(sec_centroids, q_emb)

        candidates = []
        # Track document and section counts for crowding penalty
        doc_counts = Counter()
        sec_counts = Counter()

        for rank_zero, c_idx in enumerate(top500_indices):
            cid = chunks[c_idx]["chunk_id"]
            did = chunks[c_idx]["document_id"]
            sid = chunk_sec_ids[c_idx]
            d_rank = rank_zero + 1
            d_score = float(dense_sims[c_idx])
            is_gold = cid in gold_cids

            # BM25 scores
            bm25_body = bm25_score_tokens(q_tokens, c_idx, tokenized_body, body_lens, avgdl_body, idf_body)
            bm25_heading = bm25_score_tokens(q_tokens, c_idx, tokenized_heading, heading_lens, avgdl_heading, idf_heading)
            bm25_title = bm25_score_tokens(q_tokens, c_idx, tokenized_title, title_lens, avgdl_title, idf_title)

            # Document and section centroid scores
            doc_score = float(doc_sims[doc_id_to_idx[did]])
            sec_score = float(sec_sims[sec_id_to_idx[sid]])

            # Lexical metrics
            cand_tokens = tokenized_body[c_idx]
            cand_token_set = set(cand_tokens)
            inter = q_token_set & cand_token_set
            containment = len(inter) / max(len(q_token_set), 1)
            jaccard = len(inter) / max(len(q_token_set | cand_token_set), 1)

            # Domain specific overlap
            abbrev_overlap = len(q_abbrev_exp_set & cand_token_set) / max(len(q_abbrev_exp_set), 1) if q_abbrev_exp_set else 0.0
            med_overlap = len(q_med_terms & cand_token_set) / max(len(q_med_terms), 1) if q_med_terms else 0.0
            
            cand_nums = set(re.findall(r"\b\d+(?:\.\d+)?\b", chunk_texts[c_idx].lower()))
            num_overlap = len(q_nums & cand_nums) / max(len(q_nums), 1) if q_nums else 0.0
            
            unit_overlap = len(q_units & cand_token_set) / max(len(q_units), 1) if q_units else 0.0
            cutoff_overlap = len(q_cutoffs & cand_token_set) / max(len(q_cutoffs), 1) if q_cutoffs else 0.0

            # Crowding penalty (redundancy)
            doc_prior_count = doc_counts[did]
            sec_prior_count = sec_counts[sid]
            doc_counts[did] += 1
            sec_counts[sid] += 1
            crowding_penalty = 1.0 / (1.0 + 0.1 * doc_prior_count + 0.2 * sec_prior_count)

            candidates.append({
                "chunk_idx": c_idx,
                "chunk_id": cid,
                "document_id": did,
                "section_id": sid,
                "dense_score": d_score,
                "dense_rank": d_rank,
                "bm25_body": bm25_body,
                "bm25_heading": bm25_heading,
                "bm25_title": bm25_title,
                "doc_score": doc_score,
                "sec_score": sec_score,
                "containment": containment,
                "jaccard": jaccard,
                "abbrev_overlap": abbrev_overlap,
                "med_overlap": med_overlap,
                "num_overlap": num_overlap,
                "unit_overlap": unit_overlap,
                "cutoff_overlap": cutoff_overlap,
                "crowding_penalty": crowding_penalty,
                "is_gold": is_gold
            })

        # Add BM25 ranks within B500
        for feat, rank_name in [("bm25_body", "bm25_body_rank"), ("bm25_heading", "bm25_heading_rank"),
                                ("bm25_title", "bm25_title_rank"), ("doc_score", "doc_rank"),
                                ("sec_score", "sec_rank")]:
            cands_sorted = sorted(candidates, key=lambda c: -c[feat])
            for r, c in enumerate(cands_sorted):
                c[rank_name] = r + 1

        queries_data.append({
            "query_id": it["query_id"],
            "query": q_text,
            "split_group_key": it.get("split_group_key", f"SGK_{it['query_id']}"),
            "candidates": candidates
        })

    # 9. 5-Fold Query-Grouped Evaluation of Each Feature and Bounded Combination
    print("Evaluating individual features and bounded combinations via 5-fold CV...")
    group_keys = sorted(list(set(qd["split_group_key"] for qd in queries_data)))
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # Feature Configurations to evaluate:
    configs = {
        "F01_Dense_Only": lambda c: c["dense_score"],
        "F02_BM25_Body_Only": lambda c: c["bm25_body"],
        "F03_BM25_Title_Only": lambda c: c["bm25_title"],
        "F04_BM25_Heading_Only": lambda c: c["bm25_heading"],
        "F05_Doc_Score_Only": lambda c: c["doc_score"],
        "F06_Section_Centroid_Only": lambda c: c["sec_score"],
        "F07_Lexical_Containment_Only": lambda c: c["containment"],
        "F08_Lexical_Jaccard_Only": lambda c: c["jaccard"],
        "F09_Abbrev_Expansion_Only": lambda c: c["abbrev_overlap"],
        "F10_Medical_Term_Only": lambda c: c["med_overlap"],
        "F11_Numeric_Overlap_Only": lambda c: c["num_overlap"],
        "F12_Unit_Overlap_Only": lambda c: c["unit_overlap"],
        "F13_Cutoff_Overlap_Only": lambda c: c["cutoff_overlap"],
        "F14_Redundancy_Crowding_Only": lambda c: c["crowding_penalty"],
        # Bounded Combinations
        "C01_TwoWay_RRF_Dense_BM25Body": lambda c: 1.0 / (60 + c["dense_rank"]) + 1.0 / (60 + c["bm25_body_rank"]),
        "C02_P3_Baseline_RRF": lambda c: 1.0 / (60 + c["dense_rank"]) + 1.5 / (60 + c["bm25_body_rank"]),
        "C03_ThreeWay_RRF_Dense_BM25_Section": lambda c: (
            1.0 / (60 + c["dense_rank"]) + 1.5 / (60 + c["bm25_body_rank"]) + 0.5 / (60 + c["sec_rank"])
        ),
        "C04_FourWay_RRF_Dense_BM25_Sec_Head": lambda c: (
            1.0 / (60 + c["dense_rank"]) + 1.5 / (60 + c["bm25_body_rank"]) +
            0.5 / (60 + c["sec_rank"]) + 0.3 / (60 + c["bm25_heading_rank"])
        ),
        "C05_Hybrid_Dense_BM25_Crowding": lambda c: (
            (1.0 / (60 + c["dense_rank"]) + 1.5 / (60 + c["bm25_body_rank"])) * c["crowding_penalty"]
        ),
        "C06_Feature_Oracle_V2_Full_Bounded": lambda c: (
            1.0 / (60 + c["dense_rank"]) +
            1.5 / (60 + c["bm25_body_rank"]) +
            0.5 / (60 + c["sec_rank"]) +
            0.3 / (60 + c["bm25_heading_rank"]) +
            0.2 * c["jaccard"] +
            0.2 * c["med_overlap"] +
            0.15 * c["num_overlap"] +
            0.1 * c["abbrev_overlap"]
        ) * c["crowding_penalty"]
    }

    results = {}

    for cfg_name, score_fn in configs.items():
        t0 = time.time()
        fold_cov20 = []
        all_ranks = []
        all_rr = []

        for fold_idx, (train_group_idx, val_group_idx) in enumerate(kf.split(group_keys)):
            val_groups = set(group_keys[i] for i in val_group_idx)
            fold_queries = [qd for qd in queries_data if qd["split_group_key"] in val_groups]
            fold_cov20_cnt = 0

            for qd in fold_queries:
                ranked = sorted(qd["candidates"], key=lambda c: -score_fn(c))
                best_rank = 999
                for r, c in enumerate(ranked):
                    if c["is_gold"]:
                        best_rank = min(best_rank, r + 1)
                all_ranks.append(best_rank)
                all_rr.append(1.0 / best_rank if best_rank <= 500 else 0.0)
                if best_rank <= 20:
                    fold_cov20_cnt += 1

            fold_pct = fold_cov20_cnt / len(fold_queries) * 100.0
            fold_cov20.append(fold_pct)

        elapsed = (time.time() - t0) * 1000.0 / n_queries
        ranks_arr = np.array(all_ranks)
        cov20_total = int(np.sum(ranks_arr <= 20))
        cov50_total = int(np.sum(ranks_arr <= 50))
        mrr = float(np.mean(all_rr))
        med_rank = float(np.median(ranks_arr))
        p75_rank = float(np.percentile(ranks_arr, 75))
        p90_rank = float(np.percentile(ranks_arr, 90))
        mean_fold = float(np.mean(fold_cov20))
        std_fold = float(np.std(fold_cov20))
        worst_fold = float(np.min(fold_cov20))

        results[cfg_name] = {
            "cov20_count": cov20_total,
            "cov20_pct": round(cov20_total / n_queries * 100.0, 2),
            "cov50_count": cov50_total,
            "cov50_pct": round(cov50_total / n_queries * 100.0, 2),
            "mrr": round(mrr, 4),
            "median_gold_rank": med_rank,
            "p75_gold_rank": p75_rank,
            "p90_gold_rank": p90_rank,
            "fold_by_fold_cov20": [round(x, 2) for x in fold_cov20],
            "mean_cov20": round(mean_fold, 2),
            "std_cov20": round(std_fold, 2),
            "worst_fold_cov20": round(worst_fold, 2),
            "latency_ms_per_query": round(elapsed, 2)
        }

    # Summary table
    print("\nFeature Oracle V2 Stability Summary (Query-Grouped 5-Fold CV on N=80):")
    print(f"{'Configuration':<38} | {'Cov@20':<8} | {'Cov@50':<8} | {'MRR':<6} | {'Med':<5} | {'p75':<5} | {'Worst':<6} | {'Std':<5}")
    print("-" * 95)
    for cfg, r in sorted(results.items(), key=lambda x: -x[1]["cov20_pct"]):
        print(f"{cfg:<38} | {r['cov20_pct']:>6.1f}% | {r['cov50_pct']:>6.1f}% | {r['mrr']:>6.4f} | {r['median_gold_rank']:>5.1f} | {r['p75_gold_rank']:>5.1f} | {r['worst_fold_cov20']:>5.1f}% | {r['std_cov20']:>5.2f}")

    report = {
        "report_type": "MEDICALPLAB_RENAL_V6_PHASE3_FEATURE_ORACLE_V2",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_protocol": "5_FOLD_QUERY_GROUPED_CV",
        "n_queries": n_queries,
        "candidate_pool_size": 500,
        "feature_results": results,
        "key_findings": {
            "dense_only_cov20": results["F01_Dense_Only"]["cov20_pct"],
            "bm25_body_only_cov20": results["F02_BM25_Body_Only"]["cov20_pct"],
            "p3_baseline_cov20": results["C02_P3_Baseline_RRF"]["cov20_pct"],
            "full_bounded_oracle_cov20": results["C06_Feature_Oracle_V2_Full_Bounded"]["cov20_pct"],
            "full_bounded_worst_fold": results["C06_Feature_Oracle_V2_Full_Bounded"]["worst_fold_cov20"],
            "oracle_gain_over_dense": round(results["C06_Feature_Oracle_V2_Full_Bounded"]["cov20_pct"] - results["F01_Dense_Only"]["cov20_pct"], 2),
            "oracle_gain_over_p3": round(results["C06_Feature_Oracle_V2_Full_Bounded"]["cov20_pct"] - results["C02_P3_Baseline_RRF"]["cov20_pct"], 2)
        }
    }

    report_path = REPORTS_V6_DIR / "renal_v6_phase3_feature_oracle_v2_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_sha = compute_sha256(report_path)
    (REPORTS_V6_DIR / "renal_v6_phase3_feature_oracle_v2_report.json.sha256").write_text(report_sha + "\n", encoding="utf-8")

    print(f"\nPhase 3 Complete. Report written to {report_path}")
    print(f"Report SHA256: {report_sha}")

if __name__ == "__main__":
    main()
