"""Phase 15 — Freeze Final Retrieval Configuration per Mission §44.

Generates reports/renal_v2_final_config.json and its SHA256 sidecar.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "reports" / "renal_v2_final_config.json"
REG_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CORPUS_SNAPSHOT = ROOT / "Data" / "metadata" / "corpus_renal_snapshot_v2.json"

registry = json.loads(REG_PATH.read_text(encoding="utf-8"))
active_sources = [d["document_id"] for d in registry["documents"] if d.get("v2_active", True)]

# Generate corpus snapshot
corpus_manifest = {
    "corpus_id": "RENAL-CORPUS-V2-FROZEN",
    "n_active_sources": len(active_sources),
    "active_sources": active_sources,
    "registry_sha256": hashlib.sha256(REG_PATH.read_bytes()).hexdigest(),
}
CORPUS_SNAPSHOT.write_text(json.dumps(corpus_manifest, indent=2) + "\n", encoding="utf-8")
corpus_sha = hashlib.sha256(CORPUS_SNAPSHOT.read_bytes()).hexdigest()

config = {
    "config_id": "RENAL-V2-RETRIEVAL-CONFIG-FROZEN",
    "frozen_at": "2026-09-10T07:05:00Z",
    "status": "FROZEN_FINAL",
    "corpus_snapshot_sha256": corpus_sha,
    "n_active_sources": len(active_sources),
    "active_source_list": sorted(active_sources),
    "chunking": "B_400_overlap",
    "chunking_justification": (
        "Empirically superior across all dense matrix evaluations: Hit@1=0.3043, Hit@5=0.7391, "
        "Hit@10=0.8116, MRR=0.4705, nDCG@10=0.5532 under verified evidence-span ground truth."
    ),
    "representation": "content_only",
    "representation_justification": "Avoids topic/role token dilution in short medical embeddings.",
    "embedding_model": "Qwen/Qwen3-Embedding-0.6B",
    "embedding_model_revision": "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
    "embedding_dimension": 1024,
    "max_sequence_length": 512,
    "query_instruction": (
        "Instruct: Retrieve the medical evidence passage that directly supports this "
        "renal education query.\nQuery: "
    ),
    "query_normalization": "none",
    "bm25_retained": False,
    "bm25_decision": "DISCARDED per mission spec §30 and ablation evidence (H@1 dropped to 0.1449)",
    "hybrid_rrf_retained": False,
    "hybrid_rrf_decision": "DISCARDED per mission spec §30 and ablation evidence (H@1 dropped to 0.1304)",
    "reranker_retained": False,
    "reranker_decision": "DISCARDED per mission spec §31 and Stage B diagnostic (candidate recall capped, no gain over dense)",
    "parent_expansion_retained": True,
    "parent_expansion_decision": "RETAINED for full evidence context delivery at runtime",
    "candidate_depth": 10,
}

CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
config_sha = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
CONFIG_PATH.with_suffix(".json.sha256").write_text(f"{config_sha}  {CONFIG_PATH.name}\n", encoding="utf-8")

print(f"Frozen Retrieval Configuration:")
print(f"  Config file: {CONFIG_PATH.name}")
print(f"  FINAL_CONFIG_SHA256: {config_sha}")
print(f"  Corpus Snapshot SHA256: {corpus_sha}")
print(f"  Active sources: {len(active_sources)}")
