# MedicalPlab — GitHub Presentation & Metadata Recommendations

**Audit Date:** 2026-09-14  
**Workspace:** `MedicalPlab-productized`  
**Purpose:** Provide actionable, startup-grade GitHub repository settings recommendations for the repository maintainer.

---

## 1. Repository Description & Tagline

### Recommended One-Line Description
> **Evidence-grounded medical education platform combining adaptive undergraduate learning with fail-closed licensing preparation.**

### Character-Constrained Variant (Under 100 characters for compact cards)
> **Evidence-grounded medical learning: adaptive university track + fail-closed licensing prep.**

---

## 2. GitHub Topics (Repository Tags)

Recommended tags to optimize discovery by judges, researchers, and healthcare AI evaluators:

```
medical-ai
medical-education
rag
evidence-engine
fastapi
nextjs
qwen-reranker
bayesian-knowledge-tracing
clinical-safety
healthcare
plab
mla
python
typescript
bm25
```

---

## 3. Website & Demo URLs

- **Primary Demo Frontend:** `https://medical-plab.vercel.app`
- **Interactive Documentation Path:** `docs/DEMO_GUIDE.md`
- **API Documentation (Local):** `http://localhost:8000/docs`

---

## 4. GitHub About Section Configuration

- **Description:** `Evidence-grounded medical education platform combining adaptive undergraduate learning with fail-closed licensing preparation.`
- **Website:** `https://medical-plab.vercel.app`
- **Include in Home:**
  - [x] Releases
  - [x] Packages
  - [ ] Environments (leave unchecked unless public staging deployed)

---

## 5. Release Packaging & Tag Recommendation

For the final hackathon submission milestone:

- **Release Tag:** `v1.0.0-hackathon` (or `v1.0.0`)
- **Release Title:** `MedicalPlab v1.0.0 — Final Productized Release`
- **Release Notes Outline:**
  - **University Learning Track:** 6 questions across Renal Physiology (Glomerular filtration barrier & RAAS mechanisms), zero answer leakage, BKT adaptive mastery.
  - **PLAB V9 Licensing Preparation:** Strict cryptographic evidence provenance, 9-point blocker taxonomy (24/36 quarantined), zero unapproved questions published without GMC clinician sign-off.
  - **Canonical Evidence Engine V1.1:** Multi-channel hybrid retrieval (field-aware BM25, document routing, weighted RRF) + Qwen3-Reranker-0.6B + CentralClaimVerifier.
  - **Verified DEV Metrics:** MRR 0.8144, Hit@5 0.8485, CandidateRecall@50 0.9697, 0 / 37 unsupported DEV cases served (fail-closed abstention).
  - **Full-Stack Stack:** Next.js 16.3.4 (React 19 + Turbopack) + FastAPI + Docker.
