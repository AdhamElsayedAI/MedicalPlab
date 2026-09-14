# MedicalPlab — Git Branch Audit & Cleanup Recommendations

**Audit Date:** 2026-09-14  
**Active Work Branch:** `repo-productization-final-v1`  
**Safety Protocol:** Read-Only Audit. No remote branches or tags were deleted.

---

## 1. Executive Summary

A comprehensive inventory of local and remote branches was conducted to classify development history, identify critical evidence vaults, and recommend candidate branches for pruning post-hackathon submission.

---

## 2. Complete Branch Classification

### Tier 1: Canonical & Active Work Branches (MUST RETAIN)

| Branch | Location | Classification | Rationale |
| :--- | :--- | :--- | :--- |
| `main` / `origin/main` | Local + Remote | `ACTIVE` | Canonical primary branch of the repository. |
| `repo-productization-final-v1` | Local (Active) | `ACTIVE` | Current final productization and repository cleanup branch. |
| `release/hackathon-2026` | Local + Remote | `RELEASE` | Official submission release branch. |
| `university-track-final-v1` | Local | `RELEASE` | Accepted milestone closure for University Learning Track. |
| `rag-production-final-v1` | Local | `RELEASE` | Accepted milestone closure for Canonical Evidence Engine V1.1. |

---

### Tier 2: Canonical Evidence Vaults (MUST PRESERVE IN GITHUB HISTORY)

> [!IMPORTANT]
> The branches below contain the immutable historical cryptographic proofs, publisher evidence receipts, and dispute audit logs. They MUST NOT be deleted.

| Branch | Location | Classification | Cryptographic Role |
| :--- | :--- | :--- | :--- |
| `plab-evidence-final-v9` | Local | `HISTORICAL_EVIDENCE` | **Canonical private evidence vault** (`f62b3965c0d0f10e3c636e262365e0886c61cee8`). Anchors raw byte lengths and normalized hashes. |
| `plab-evidence-source-proof-v8` | Local | `HISTORICAL_EVIDENCE` | V8 publisher source proof audit history. |
| `plab-evidence-final-v7` | Local + Remote | `HISTORICAL_EVIDENCE` | V7 multi-source consensus evidence baseline. |
| `plab-evidence-final-v6` | Local | `HISTORICAL_EVIDENCE` | V6 cardiorespiratory audit trail. |
| `plab-evidence-truth-v5` | Local | `HISTORICAL_EVIDENCE` | V5 clinical evidence ground truth. |
| `plab-evidence-correction-v4` | Local | `HISTORICAL_EVIDENCE` | V4 clinical citation correction receipts. |
| `plab-v3-disputed`, `v4`, `v5` | Local | `HISTORICAL_EVIDENCE` | Historical record of distractor ambiguity and disputed option adjudications. |

---

### Tier 3: Merged Milestone & Historical Feature Branches (ARCHIVAL CANDIDATES)

These branches represent past development phases whose code is already integrated into `main`:

| Branch | Location | Classification | Recommendation |
| :--- | :--- | :--- | :--- |
| `ai-data-execution-v1` | Local + Remote | `HISTORICAL` | Safe to delete remotely after submission freeze. |
| `stage-b-verifier-v1` | Remote | `HISTORICAL` | Safe to delete remotely. |
| `evidence-sufficiency-v1` | Remote | `HISTORICAL` | Safe to delete remotely. |
| `stage-g-productization` | Remote | `HISTORICAL` | Safe to delete remotely. |

---

### Tier 4: Stale & Temporary Branches (SAFE PRUNING CANDIDATES)

These branches contain transient experimentation or temporary CI checks and can be safely removed from GitHub by the repository administrator:

| Branch | Location | Classification | Recommended Action |
| :--- | :--- | :--- | :--- |
| `origin/noop-check` | Remote | `STALE` / `TEMPORARY` | Delete via `git push origin --delete noop-check` |
| `origin/noop-check2` | Remote | `STALE` / `TEMPORARY` | Delete via `git push origin --delete noop-check2` |
| `origin/tmp-ignore` | Remote | `STALE` / `TEMPORARY` | Delete via `git push origin --delete tmp-ignore` |
| `codex/checkpoint-01213fb` | Local | `STALE` / `TEMPORARY` | Delete via `git branch -D codex/checkpoint-01213fb` |

---

## 3. Recommended Administrative Execution Commands (Post-Hackathon)

To execute the recommended branch hygiene post-submission:

```bash
# 1. Delete temporary / noop branches from remote
git push origin --delete noop-check
git push origin --delete noop-check2
git push origin --delete tmp-ignore

# 2. Prune obsolete historical development branches from remote
git push origin --delete stage-b-verifier-v1
git push origin --delete evidence-sufficiency-v1
git push origin --delete stage-g-productization

# 3. Clean local branch tracking
git fetch --prune
git branch -D codex/checkpoint-01213fb
```
