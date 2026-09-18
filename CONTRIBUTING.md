# Contributing to MedicalPlab

Thank you for contributing to MedicalPlab. Because this platform serves medical learners and interfaces with clinical concepts, all contributions must uphold strict safety, architectural, and verification standards.

---

## 1. Core Architectural & Safety Invariants

Every contribution must preserve the following non-negotiable boundaries:

1. **Evidence Gating & Grounding:**
   - The AI Tutor and clinical reasoning engines must strictly operate behind evidence retrieval and claim verification.
   - Never implement direct unconstrained LLM generation for medical explanations.
   - Unverified clinical propositions must trigger fail-closed behavior (`SAFE_FALLBACK`).

2. **Heuristic Cognitive Signals:**
   - Selected distractors produce provisional *heuristic reasoning signals*, never definitive diagnoses of learner competence.
   - Socratic remediation must remain bounded (maximum 3 turns) and culminate in an independent transfer test.

3. **Anatomy Asset Authority:**
   - 3D anatomical models derive exclusively from authoritative, scientifically licensed datasets (HuBMAP HRA).
   - Generative AI may emit structured scene actions (camera moves, highlighting), but **never** generate or deform scientific anatomy geometry.

4. **Clinical Content Governance:**
   - No unreviewed clinical exam material may be promoted into production.
   - PLAB candidate content remains gated behind Preview QA until reviewed and approved by an authorized clinician panel (`PLAB_GOLDEN_PROMOTION_REQUIRED = YES`).

---

## 2. Development & Branching Workflow

1. **Branching Strategy:**
   - Do not commit directly to `main`.
   - Branch from the latest `main` using descriptive prefixes:
     - `feature/` for new product capabilities
     - `fix/` for bug fixes
     - `docs/` for documentation updates
     - `refactor/` for code improvements without behavior change
2. **Quality Gates:**
   - Run the integration test suite:
     ```powershell
     python -m pytest tests/integration/ -q -p no:cacheprovider
     ```
   - Verify mobile API contract drift:
     ```powershell
     python Scripts/verify_mobile_contract_drift.py
     ```
   - Verify frontend production build:
     ```bash
     cd frontend && npm run build
     ```
3. **Pull Request Protocol:**
   - Open a PR against `main` using the repository PR template.
   - Ensure all automated CI checks pass.
   - All PRs require code review and clinical safety sign-off if modifying educational pipelines.

---

## 3. Code Quality & Standards

- **Backend:** Python 3.11 or 3.12 (pyproject.toml: ">=3.11,<3.13"), FastAPI, strict Pydantic v2 schemas, type annotations throughout.
- **Frontend:** Next.js 16 (App Router, Node.js >=20.9), React 19, TypeScript strict mode, Tailwind CSS.
- **Documentation:** Maintain exact alignment between runtime OpenAPI schemas, Postman collections, and markdown documentation.
