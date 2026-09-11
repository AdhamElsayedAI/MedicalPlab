"""Phase 1 forensic audit — historical firewall + runtime inspection."""
import hashlib
import json
import pathlib
import pickle
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# ── 1. Historical firewall SHA verification ──────────────────────────────────
print("=== HISTORICAL FIREWALL SHA VERIFICATION ===")
SPENT = {
    "V2_HELDOUT":       "evaluation/renal/renal-heldout-v2-final.json",
    "V3_HELDOUT":       "evaluation/renal/v3/renal-heldout-v3-final.json",
    "V3_SAFETY_TEST2":  "evaluation/renal/v3/renal-v3-safety-test-2.json",
    "V4_SAFETY_TEST":   "evaluation/renal/v4/renal-safety-test-v4.json",
    "V4_HELDOUT":       "evaluation/renal/v4/renal-heldout-v4-final.json",
    "V4_CLASSIFIER":    "models/renal_v4_evidence_classifier.pkl",
}
SPENT_EXPECTED_SHA = {
    "V2_HELDOUT":       "8885b21bc1174ea6a05028c03813d4aa1e72cfb5ecbd254a7e08c56bf8c29b92",
    "V3_HELDOUT":       "40c96f46be1c6547f2ffbdc29f90fb3444d48e66dfcfaae769cd3b8413082d32",
    "V3_SAFETY_TEST2":  "3fe59bb6011c5ab4c526cbcc092b8dc087709b67d3f2aaa7318acd6679dcf8eb",
    "V4_SAFETY_TEST":   "7d2069b5a1216f096b246c0c95033ef74118bc7c00d244f4debbf3c36eb6d2ad",
    "V4_HELDOUT":       "0368761712c91b068f913fef3760a2a331dfe0de735eb2ac5a77bcdef920a8c6",
    "V4_CLASSIFIER":    "54f42677b4776354740001bb35b69ecd9b7cc9851c17dacb540f046229e864de",
}
all_ok = True
for name, rel in SPENT.items():
    p = ROOT / rel
    if not p.exists():
        print(f"  MISSING: {name} at {rel}")
        all_ok = False
        continue
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    expected = SPENT_EXPECTED_SHA[name]
    ok = sha == expected
    if not ok:
        all_ok = False
    print(f"  {name}: {sha[:16]}... [{'OK' if ok else 'MISMATCH'}]")

if all_ok:
    print("  ALL HISTORICAL ARTIFACTS INTACT\n")
else:
    print("  WARNING: FIREWALL VIOLATION DETECTED\n")

# ── 2. V4 safety test report ─────────────────────────────────────────────────
rep_path = ROOT / "reports/renal_v4/renal_v4_safety_test_results.json"
rep_sha = hashlib.sha256(rep_path.read_bytes()).hexdigest()
EXPECTED_REP = "e1c58c5c1c759f0dd4052ea17f4589b256b438b6d80afc7c67a3bd27af238f39"
print(f"V4_SAFETY_TEST_REPORT SHA match: {rep_sha == EXPECTED_REP}")

# ── 3. Classifier bundle inspection ──────────────────────────────────────────
print("\n=== V4 CLASSIFIER BUNDLE INSPECTION ===")
clf_path = ROOT / "models/renal_v4_evidence_classifier.pkl"
with open(clf_path, "rb") as f:
    bundle = pickle.load(f)
print(f"  Bundle keys: {list(bundle.keys())}")
clf = bundle["model"]
scaler = bundle["scaler"]
tau = bundle.get("calibrated_threshold", 0.6886)
print(f"  Model type: {type(clf).__name__}")
print(f"  Scaler type: {type(scaler).__name__}")
print(f"  Calibrated threshold tau: {tau}")
print(f"  Feature indices: {bundle.get('feature_indices', 'all')}")

# ── 4. V4 safety config ───────────────────────────────────────────────────────
print("\n=== V4 SAFETY CONFIG ===")
safe_cfg = json.loads((ROOT / "configs/renal_v4_safety_config.json").read_bytes())
print(f"  Selected architecture: {safe_cfg['selected_architecture']}")
print(f"  Features ({len(safe_cfg['feature_schema'])}): {safe_cfg['feature_schema']}")
print(f"  Tau: {safe_cfg['operating_threshold_tau']}")
print(f"  n_positive_operational: {safe_cfg['statistical_sizing']['n_positive_operational']}")
print(f"  n_negative_operational: {safe_cfg['statistical_sizing']['n_negative_operational']}")

# ── 5. V4 retrieval config ───────────────────────────────────────────────────
print("\n=== V4 RETRIEVAL CONFIG ===")
ret_cfg = json.loads((ROOT / "configs/renal_v4_retrieval_config.json").read_bytes())
print(f"  Architecture: {ret_cfg['architecture_version']}")
print(f"  Embedding model: {ret_cfg['embedding_model']['model_id']}")
print(f"  alpha_doc_prior: {ret_cfg['first_stage_scoring']['soft_document_prior_alpha']}")
print(f"  beta_sec_prior:  {ret_cfg['first_stage_scoring']['section_structural_weight_beta']}")
print(f"  superset_budget_B: {ret_cfg['candidate_selection']['superset_budget_B']} (DIAGNOSTIC ONLY)")
print(f"  reranker_input_R: {ret_cfg['candidate_selection']['reranker_input_budget_R']}")
print(f"  selection_policy: {ret_cfg['candidate_selection']['selection_policy']}")
print(f"  Reranker: {ret_cfg['reranker']['model_id']}")

# ── 6. V3 config baseline inferred ───────────────────────────────────────────
print("\n=== V3 EFFECTIVE PARAMETERS (from source code) ===")
print("  alpha_doc_prior = 0.18")
print("  candidate_depth = 20 (direct)")
print("  Reranker: Qwen/Qwen3-Reranker-0.6B")
print("  Embedding: Qwen/Qwen3-Embedding-0.6B")
print("  No section structural channel (beta=0)")
print("  No safety classifier (raw score vs RENAL_SUFFICIENCY_THRESHOLD)")

# ── 7. Evaluation sets for V4 (metadata only) ─────────────────────────────
print("\n=== V4 EVALUATION DATASET SIZES ===")
v4_dir = ROOT / "evaluation/renal/v4"
for fname in sorted(v4_dir.glob("*.json")):
    try:
        data = json.loads(fname.read_bytes())
        n = len(data.get("queries", data if isinstance(data, list) else []))
        sha = hashlib.sha256(fname.read_bytes()).hexdigest()
        print(f"  {fname.name}: N={n}, SHA={sha[:16]}...")
    except Exception as e:
        print(f"  {fname.name}: ERROR {e}")
