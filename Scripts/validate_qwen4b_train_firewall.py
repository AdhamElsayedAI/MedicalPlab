from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path
from typing import Any
from qwen4b_adaptation_common import ROOT, load_config, root_path, normalize_text, jaccard, atomic_json, sha256_file


def walk_records(obj: Any):
    if isinstance(obj, dict):
        if any(k in obj for k in ("query", "question", "stem", "canonical_claim", "atomic_claim", "gold_chunk_ids", "exact_gold_chunk_ids", "semantic_support_chunk_ids")):
            yield obj
        for v in obj.values():
            yield from walk_records(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_records(v)


def _gold_ids(r: dict[str, Any]) -> tuple[str, ...]:
    vals = []
    for k in ("gold_chunk_ids", "exact_gold_chunk_ids", "semantic_support_chunk_ids", "gold_passage_ids"):
        v = r.get(k, [])
        if isinstance(v, list):
            vals.extend(str(x) for x in v if x)
        elif v:
            vals.append(str(v))
    return tuple(sorted(set(vals)))


def _training_signature(r: dict[str, Any]) -> tuple[str, str, tuple[str, ...]]:
    query = next((r.get(k) for k in ("query", "question", "stem") if isinstance(r.get(k), str) and r.get(k).strip()), "")
    claim = next((r.get(k) for k in ("canonical_claim", "atomic_claim", "claim") if isinstance(r.get(k), str) and r.get(k).strip()), "")
    return normalize_text(query), normalize_text(claim), _gold_ids(r)


def _approved_source_signatures(cfg) -> set[tuple[str, str, tuple[str, ...]]]:
    src = root_path(cfg["data"]["source_pool"])
    try:
        obj = json.loads(src.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"KNOWN_TRAINING_SOURCE_POOL_UNREADABLE path={src}") from e
    sigs = {
        _training_signature(r)
        for r in walk_records(obj)
        if _training_signature(r)[0]
    }
    if not sigs:
        raise RuntimeError(f"KNOWN_TRAINING_SOURCE_POOL_EMPTY path={src}")
    return sigs


def validated_known_training_artifacts(cfg):
    configured = cfg["data"].get("known_training_artifacts", [])
    if not configured:
        return []
    approved = _approved_source_signatures(cfg)
    validated = []
    for rel in configured:
        rel_path = Path(str(rel))
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise RuntimeError(f"KNOWN_TRAINING_ARTIFACT_PATH_INVALID path={rel}")
        p = ROOT / rel_path
        if not p.is_file():
            raise RuntimeError(f"KNOWN_TRAINING_ARTIFACT_MISSING path={rel}")
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            raise RuntimeError(f"KNOWN_TRAINING_ARTIFACT_UNREADABLE path={rel}") from e
        records = [
            r for r in walk_records(obj)
            if any(isinstance(r.get(k), str) and r.get(k).strip() for k in ("query", "question", "stem"))
        ]
        if not records:
            raise RuntimeError(f"KNOWN_TRAINING_ARTIFACT_EMPTY path={rel}")
        for r in records:
            qid = str(r.get("query_id", "")).strip()
            if "-TRN-" not in qid.upper():
                raise RuntimeError(
                    f"KNOWN_TRAINING_ARTIFACT_VALIDATION_FAILED path={rel} query_id={qid or '<missing>'} reason=NON_TRAIN_ID"
                )
            sig = _training_signature(r)
            if sig not in approved:
                raise RuntimeError(
                    f"KNOWN_TRAINING_ARTIFACT_VALIDATION_FAILED path={rel} query_id={qid} reason=NOT_IN_APPROVED_SOURCE_POOL"
                )
        validated.append(p)
    return validated


def eval_files(cfg):
    files = set()
    for pat in cfg["data"]["forbidden_eval_globs"]:
        files.update(ROOT.glob(pat))
    known_training = {p.resolve() for p in validated_known_training_artifacts(cfg)}
    return sorted(
        p for p in files
        if p.is_file() and p.suffix == ".json" and p.resolve() not in known_training
    )


def extract_eval(cfg):
    queries = []
    claims = []
    spans = []
    passage_ids = set()
    sources = []
    for p in eval_files(cfg):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        source = str(p.relative_to(ROOT))
        sources.append(source)
        for r in walk_records(obj):
            for k in ("query", "question", "stem"):
                if isinstance(r.get(k), str):
                    queries.append((r[k], source))
            for k in ("canonical_claim", "atomic_claim", "claim"):
                if isinstance(r.get(k), str):
                    claims.append((r[k], source))
            for k in ("evidence_span_text", "evidence_span", "gold_passage", "positive_passage"):
                if isinstance(r.get(k), str):
                    spans.append((r[k], source))
            for k in ("gold_chunk_ids", "exact_gold_chunk_ids", "semantic_support_chunk_ids", "gold_passage_ids"):
                v = r.get(k, [])
                passage_ids.update(v if isinstance(v, list) else [v])
    return queries, claims, spans, {str(x) for x in passage_ids if x}, sources


def adjacent_ids(cid: str) -> set[str]:
    m = re.match(r"(.+-C)(\d+)$", cid)
    if not m:
        return set()
    n = int(m.group(2))
    width = len(m.group(2))
    return {f"{m.group(1)}{i:0{width}d}" for i in (n - 1, n + 1) if i >= 0}


def _negative_leak_reasons(hid: str, htext: str, eids: set[str], ns: dict[str, tuple[str, str]]) -> list[dict[str, Any]]:
    reasons = []
    if hid in eids:
        reasons.append({"type": "hard_negative_overlaps_eval_gold", "passage_id": hid})
    if adjacent_ids(hid) & eids:
        reasons.append({"type": "hard_negative_adjacent_eval_gold", "passage_id": hid})
    hnorm = normalize_text(htext)
    if hnorm and hnorm in ns:
        reasons.append({"type": "hard_negative_same_evidence_span", "passage_id": hid, "source": ns[hnorm][1]})
    return reasons


def lexical_firewall(train, cfg):
    eq, ec, es, eids, sources = extract_eval(cfg)
    nq = {normalize_text(q): (q, s) for q, s in eq}
    nc = {normalize_text(c): (c, s) for c, s in ec}
    ns = {normalize_text(s): (s, src) for s, src in es}
    threshold = cfg["data"]["near_duplicate_threshold"]
    excluded = []
    clean = []
    sanitized = []

    for r in train:
        reasons = []
        qn = normalize_text(r["query"])
        cn = normalize_text(r.get("atomic_claim", "") or "")
        pn = normalize_text(r["positive_passage"])
        if qn in nq:
            reasons.append({"type": "exact_or_normalized_query_overlap", "source": nq[qn][1]})
        if cn and cn in nc:
            reasons.append({"type": "same_atomic_claim", "source": nc[cn][1]})
        if pn in ns:
            reasons.append({"type": "same_evidence_span", "source": ns[pn][1]})
        pid = r["positive_passage_id"]
        if pid in eids:
            reasons.append({"type": "same_passage_or_gold", "passage_id": pid})
        if adjacent_ids(pid) & eids:
            reasons.append({"type": "adjacent_evidence_leakage", "passage_id": pid})

        safe_ids = []
        safe_passages = []
        safe_categories = []
        removed = []
        ids = r.get("hard_negative_ids", [])
        passages = r.get("hard_negative_passages", [])
        categories = r.get("hard_negative_categories", [])
        for i, (hid, htext) in enumerate(zip(ids, passages)):
            neg_reasons = _negative_leak_reasons(hid, htext, eids, ns)
            if neg_reasons:
                removed.append({"passage_id": hid, "reasons": neg_reasons})
                continue
            safe_ids.append(hid)
            safe_passages.append(htext)
            safe_categories.append(categories[i] if i < len(categories) else "unspecified")

        if removed:
            sanitized.append({
                "query_id": r["query_id"],
                "removed_hard_negative_count": len(removed),
                "kept_hard_negative_count": len(safe_ids),
                "removed_hard_negatives": removed,
            })

        if not safe_ids:
            reasons.append({"type": "no_safe_hard_negatives_after_firewall"})

        if not reasons:
            best = max(
                ((jaccard(r["query"], q), src, q) for q, src in eq),
                default=(0.0, "", ""),
                key=lambda x: x[0],
            )
            if best[0] >= threshold:
                reasons.append({"type": "near_duplicate_query", "score": round(best[0], 4), "source": best[1]})

        if reasons:
            excluded.append({"query_id": r["query_id"], "reasons": reasons})
        else:
            rr = dict(r)
            rr["hard_negative_ids"] = safe_ids
            rr["hard_negative_passages"] = safe_passages
            rr["hard_negative_categories"] = safe_categories
            clean.append(rr)
    return clean, excluded, sources, sanitized


def _encode_queries(model, texts, prompt):
    import numpy as np
    if not texts:
        return np.empty((0, 0), dtype=np.float32)
    arr = np.asarray(
        model.encode(texts, prompt=prompt, batch_size=4, normalize_embeddings=True, show_progress_bar=False),
        dtype=np.float32,
    )
    if arr.ndim != 2 or arr.shape[0] != len(texts) or arr.shape[1] <= 0:
        raise RuntimeError(f"SEMANTIC_EMBEDDING_SHAPE_INVALID expected_rows={len(texts)} observed_shape={arr.shape}")
    return arr


def semantic_check(clean, cfg):
    if not clean:
        return clean, []
    import gc
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import BitsAndBytesConfig
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA_NOT_AVAILABLE")
    eq, _, _, _, _ = extract_eval(cfg)
    texts = [q for q, _ in eq]
    if not texts:
        return clean, []
    mcfg = cfg["model"]
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = SentenceTransformer(
        mcfg["id"],
        revision=mcfg["revision"],
        model_kwargs={"quantization_config": bnb, "device_map": {"": "cuda:0"}, "torch_dtype": torch.float16},
        trust_remote_code=True,
    )
    try:
        prompt = mcfg["prompt"]
        tq = _encode_queries(model, [r["query"] for r in clean], prompt)
        eqe = _encode_queries(model, texts, prompt)
        if tq.shape[1] != eqe.shape[1]:
            raise RuntimeError(f"SEMANTIC_EMBEDDING_DIMENSION_MISMATCH train={tq.shape} eval={eqe.shape}")
        sims = tq @ eqe.T
        threshold = cfg["data"]["semantic_near_duplicate_threshold"]
        keep = []
        excluded = []
        for i, r in enumerate(clean):
            j = int(sims[i].argmax())
            score = float(sims[i, j])
            if score >= threshold:
                excluded.append({"query_id": r["query_id"], "reasons": [{"type": "semantic_near_duplicate", "score": round(score, 4), "eval_query": texts[j]}]})
            else:
                keep.append(r)
        return keep, excluded
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()


def _reason_counts(excluded):
    c = Counter()
    for item in excluded:
        for reason in item.get("reasons", []):
            c[reason.get("type", "unknown")] += 1
    return dict(sorted(c.items()))


def _ignored_training_artifacts(cfg):
    return [str(p.relative_to(ROOT)) for p in validated_known_training_artifacts(cfg)]


def _write_empty_report(cfg, train, before, excluded, sources, sanitized, semantic_status, lexical_clean_n):
    report = {
        "status": "TRAIN_FIREWALL_EMPTY",
        "input_n": len(train),
        "lexical_clean_n": lexical_clean_n,
        "clean_n": 0,
        "excluded_n": len(excluded),
        "excluded": excluded,
        "exclusion_reason_counts": _reason_counts(excluded),
        "sanitized_record_n": len(sanitized),
        "removed_hard_negative_n": sum(x["removed_hard_negative_count"] for x in sanitized),
        "sanitized_hard_negatives": sanitized,
        "eval_sources": sources,
        "validated_training_artifacts_ignored": _ignored_training_artifacts(cfg),
        "input_train_sha256": before,
        "train_sha256": None,
        "semantic_check": semantic_status,
        "input_train_preserved": True,
    }
    atomic_json(root_path(cfg["data"]["firewall_report"]), report)
    return report


def run(cfg, skip_semantic=False):
    train_path = root_path(cfg["data"]["train_output"])
    train = json.loads(train_path.read_text(encoding="utf-8"))
    before = sha256_file(train_path)
    clean, excluded, sources, sanitized = lexical_firewall(train, cfg)
    lexical_clean_n = len(clean)

    if not clean:
        _write_empty_report(
            cfg, train, before, excluded, sources, sanitized,
            "NOT_RUN_EMPTY_AFTER_LEXICAL", lexical_clean_n,
        )
        raise RuntimeError(
            f"TRAIN_FIREWALL_EMPTY: lexical/provenance firewall removed all {len(train)} TRAIN items; "
            f"original train artifact preserved"
        )

    semantic_status = "SKIPPED" if skip_semantic else "QWEN4B_COSINE"
    if not skip_semantic:
        clean, semantic_ex = semantic_check(clean, cfg)
        excluded.extend(semantic_ex)

    if not clean:
        _write_empty_report(
            cfg, train, before, excluded, sources, sanitized,
            semantic_status, lexical_clean_n,
        )
        raise RuntimeError(
            f"TRAIN_FIREWALL_EMPTY: semantic firewall removed all {lexical_clean_n} lexical-clean TRAIN items; "
            f"original train artifact preserved"
        )

    clean_sha = atomic_json(train_path, clean)
    report = {
        "status": "PASS",
        "input_n": len(train),
        "lexical_clean_n": lexical_clean_n,
        "clean_n": len(clean),
        "excluded_n": len(excluded),
        "excluded": excluded,
        "exclusion_reason_counts": _reason_counts(excluded),
        "sanitized_record_n": len(sanitized),
        "removed_hard_negative_n": sum(x["removed_hard_negative_count"] for x in sanitized),
        "sanitized_hard_negatives": sanitized,
        "eval_sources": sources,
        "validated_training_artifacts_ignored": _ignored_training_artifacts(cfg),
        "input_train_sha256": before,
        "train_sha256": clean_sha,
        "semantic_check": semantic_status,
        "input_train_preserved": False,
    }
    atomic_json(root_path(cfg["data"]["firewall_report"]), report)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--skip-semantic", action="store_true")
    a = ap.parse_args()
    print(json.dumps(run(load_config(a.config), a.skip_semantic), indent=2))


if __name__ == "__main__":
    main()
