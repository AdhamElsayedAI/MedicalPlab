# Qwen3-Embedding-4B domain adaptation runbook

This experiment is the single authorized retrieval adaptation after `GENUINE_RETRIEVAL_GAP_CONFIRMED`. It does not modify production (`QwenRenalRetrieverV3`, runtime `v3`) and it never trains on PRODUCT_DEV_V3.

## Scientific firewall

The builder accepts only `VERIFIED_SAFE_UNSPENT` records from the tracked V5 clean TRAIN pool. Positives are re-resolved against tracked 400-token renal evidence chunks and source spans must occur in the positive passage. Hard negatives are mined only from the source corpus; PRODUCT_DEV_V3 is not read by the builder.

Before CUDA training, the firewall compares TRAIN against frozen development/heldout/product/OOD artifacts for exact/normalized queries, lexical near duplicates, atomic claims, evidence spans, passage IDs, gold IDs and adjacent chunks. The local run additionally performs a Qwen3-Embedding-4B cosine near-duplicate exclusion. The firewall only removes TRAIN records; it never changes evaluation data.

## One command

From the repository root in PowerShell:

```powershell
.\Scripts\run_qwen4b_domain_adaptation.ps1
```

The launcher follows the repository's existing Python 3.12 + `.renal_env` convention. It refuses CPU fallback. Missing PEFT-layer packages are installed into `.qwen4b_env`; torch is never replaced by the launcher.

## Fixed model/configuration

- Base: `Qwen/Qwen3-Embedding-4B`
- Revision/tokenizer revision: `5cf2132abc99cad020ac570b19d031efec650f2b`
- 4-bit NF4, double quantization, fp16 compute
- PEFT LoRA `FEATURE_EXTRACTION`, rank 8, alpha 16, dropout 0.05, `q_proj` + `v_proj`
- Max sequence length 256
- Micro-batch 1, gradient accumulation 8
- One epoch, LR 1e-4
- Objective: two-way InfoNCE (`query, positive, explicit hard negative`)

A two-step CUDA sanity update runs first and is discarded. The full run starts from a fresh adapter or resumes the latest atomic complete checkpoint.

## Outputs

Generated files are under `artifacts/qwen4b_domain_adaptation/` and are intentionally git-ignored:

- `train.json`
- `firewall_report.json`
- `environment_report.json`
- `sanity_report.json`
- `adapter/`
- `checkpoints/checkpoint-step-*/`
- `training_report.json`
- `evaluation_report.json`
- `evaluation_report.md`
- `gate_result.json`

If the 6 GB GPU cannot run the exact adaptation, the training report records `LOCAL_GPU_MEMORY_BLOCKER_CONFIRMED` with the CUDA error and reproducibility configuration. No model substitution is allowed.
