# MedicalPlab — Team Handoff & Role Entry Points
**Central Handoff Document for Engineering, Mobile, Presentation, and Clinical Teams**

Welcome to the MedicalPlab team handoff. This document establishes direct entry points for each discipline so you can immediately find what you need without digging through historical engineering reports.

---

## 1. Backend Developers

**Objective:** Run, maintain, test, and containerize the authoritative FastAPI intelligence core.

- **Primary Entrypoint:** [`production_main.py`](../../production_main.py)
- **Architecture Reference:** [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)
- **RAG & Evidence Engine:** [`docs/AI_SYSTEM.md`](../AI_SYSTEM.md)
- **Deployment & Containers:** [`docs/DEPLOYMENT.md`](../DEPLOYMENT.md)
- **Key Test Suites:**
  - `python -m pytest tests/integration/ -q -p no:cacheprovider` (23/23 integration tests)
  - `python -m pytest tests/integration/test_mobile_api_contract.py -q` (12/12 mobile contract tests)
- **Core Command:**
  ```powershell
  $env:PYTHONPATH="src;."; $env:MEDICALPLAB_RUNTIME_MODE="pilot"; $env:MEDICALPLAB_PLAB_PREVIEW_QA="1"; python -m uvicorn production_main:app --host 127.0.0.1 --port 8000 --workers 1
  ```

---

## 2. Frontend Developers

**Objective:** Maintain and evolve the premium Next.js 16 / React 19 learning application.

- **Primary Codebase:** [`frontend/`](../../frontend)
- **Application App Router:** [`frontend/src/app/`](../../frontend/src/app)
- **3D Anatomy Lab:** [`frontend/src/features/anatomy/`](../../frontend/src/features/anatomy)
- **API Client & Auth:** [`frontend/src/lib/api-client.ts`](../../frontend/src/lib/api-client.ts)
- **Build & Dev:**
  ```bash
  cd frontend
  npm install
  npm run dev      # Local development on http://localhost:3000
  npm run build    # Production build verification (0 TS / build errors required)
  npm run start -- -p 3000
  ```

---

## 3. Mobile Developers

**Objective:** Integrate iOS, Android, and React Native mobile clients against the frozen backend REST contract.

- **Fast Track Guide:** [`docs/mobile-handoff/START_HERE.md`](../mobile-handoff/START_HERE.md)
- **Comprehensive API Handoff:** [`docs/mobile-handoff/MOBILE_DEVELOPER_HANDOFF.md`](../mobile-handoff/MOBILE_DEVELOPER_HANDOFF.md)
- **Endpoint Quick Matrix:** [`docs/mobile-handoff/API_CONTRACT.md`](../mobile-handoff/API_CONTRACT.md)
- **OpenAPI 3.1.0 Specification:** [`docs/mobile-handoff/openapi.json`](../mobile-handoff/openapi.json)
- **Postman Artifacts:**
  - [`MedicalPlab.mobile.postman_collection.json`](../mobile-handoff/MedicalPlab.mobile.postman_collection.json)
  - [`MedicalPlab.mobile.postman_environment.json`](../mobile-handoff/MedicalPlab.mobile.postman_environment.json)
- **Key Identity Invariant:** All learner requests require `X-User-Id` header (identity-partitioning for pilot/demo).

---

## 4. Presenters, Mentors & Demo Leads

**Objective:** Conduct flawless, repeatable, end-to-end 2–4 minute product demonstrations.

- **Master Runbook:** [`docs/demo/FINAL_DEMO_RUNBOOK.md`](../demo/FINAL_DEMO_RUNBOOK.md)
- **Failure Recovery Guide:** [`docs/demo/DEMO_FAILURE_RECOVERY.md`](../demo/DEMO_FAILURE_RECOVERY.md)
- **Certified Screenshot Gallery:** [`docs/demo/final-showcase/README.md`](../demo/final-showcase/README.md)
- **Key Demo Journey (~3m 40s):**
  1. Home Hub & Cognitive Loop Animation
  2. Preclinical University Practice (`UNI-RENAL-001` Option B)
  3. Socratic Remediation & Held-out Transfer Assessment (`UNI-RENAL-001-T` Option A)
  4. Evidence-Grounded AI Tutor & Verified Citations
  5. 3D Spatial Anatomy Guided Tour & Challenge
  6. Unified Learner Progress & PLAB Preview QA

---

## 5. Clinical Reviewers & Faculty

**Objective:** Audit evidence provenance, medical accuracy, question safety, and governance.

- **Clinical Safety Framework:** [`docs/CLINICAL_SAFETY.md`](../CLINICAL_SAFETY.md)
- **PLAB Provenance & Governance:** [`docs/PLAB_PROVENANCE_AND_DATA_GOVERNANCE.md`](../PLAB_PROVENANCE_AND_DATA_GOVERNANCE.md)
- **Third-Party 3D Anatomy Notices:** [`THIRD_PARTY_NOTICES_ANATOMY.md`](../../THIRD_PARTY_NOTICES_ANATOMY.md)
- **Governance Truth:**
  - 36 candidate questions available under Preview QA for institutional review.
  - Golden released count: 0 (fail-closed; clinician panel promotion required before public clinical release).
  - Open Access PubMed Central (CC-BY) literature backing all clinical tutor claims.
