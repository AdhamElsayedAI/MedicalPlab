# Repository Handoff & Evaluator Communications

> **Standardized submission text for hackathon portals, judge correspondence, and technical reviewers.**

---

## Version A: Ultra-Short Submission Text

*(Ideal for: Submission portal text fields, short-form pitch entries, social cards)*

> **Project Name:** MedicalPlab  
> **Tagline:** MedicalPlab does not only answer students. It learns how students learn.  
> **Repository:** https://github.com/AdhamElsayedAI/MedicalPlab  
> **Quickstart:** [docs/LOCAL_RUN_GUIDE.md](../LOCAL_RUN_GUIDE.md)  
>
> **Summary:**  
> MedicalPlab is an adaptive, evidence-grounded medical learning platform. Unlike generic AI chatbots that simply provide answers, MedicalPlab analyzes learner mistakes to detect cognitive reasoning patterns, conducts bounded Socratic remediation, verifies comprehension through independent held-out transfer challenges, and anchors physiological concepts in 3D Cognitive Anatomy. Every clinical explanation is grounded in PubMed Central open-access literature with fail-closed verification. The platform runs 100% locally with zero cloud dependencies and includes a certified mobile API contract.

---

## Version B: Professional Email / Form Message

*(Ideal for: Formal hackathon submission forms, mentor outreach, accelerator applications)*

> **Subject:** MedicalPlab — Hackathon / Startup Track Submission
>
> Dear Judges and Reviewers,
>
> We are excited to present **MedicalPlab**, an adaptive, evidence-grounded medical learning platform designed for medical students and educational institutions.
>
> **The Problem:**  
> Today, medical students widely use generic LLMs to study, but conversational AI does not understand learning. Standard chatbots fail to track mastery trajectories, view mistakes as binary errors rather than cognitive reasoning patterns, cannot verify transfer, and risk medical hallucinations without audit trails.
>
> **The Solution:**  
> MedicalPlab bridges AI and clinical education through a closed-loop cognitive architecture:
> 1. **Learner Attempt:** The student tackles clinical vignettes across core medical modules.
> 2. **Reasoning-Pattern Signal:** Distractor choices generate provisional cognitive hypotheses (e.g. confusing enzyme activation cascades) without diagnostically labeling the student.
> 3. **Bounded Socratic Remediation:** The AI acts as a tutor in a strictly bounded 3-turn dialogue, guiding deduction without leaking answers.
> 4. **Independent Transfer Verification:** Transfer confirmation is certified only after the student independently solves an unprompted, held-out clinical challenge (`UNI-RENAL-001-T`).
> 5. **Evidence Grounding & Cognitive Anatomy:** Clinical explanations are synthesized from retrieved peer-reviewed PubMed Central CC-BY literature and validated via NLI entailment checks, while spatial anatomy provides deterministic raycast challenge scoring.
>
> **Engineering Rigor:**  
> MedicalPlab is engineered for complete local reproducibility:
> - **Zero Cloud Costs:** Runs locally on standard CPUs with $0 cloud, 0 GPU, and 0 paid LLM keys required.
> - **Verified Quality:** 23/23 backend integration tests, 12/12 mobile contract tests, and 8/8 GitHub Actions CI checks passing.
> - **API Contract:** 43 paths / 44 operations certified via OpenAPI 3.1.0 with complete Postman harnesses.
>
> **Key Links:**  
> - **GitHub Repository:** https://github.com/AdhamElsayedAI/MedicalPlab  
> - **Local Run Guide:** [docs/LOCAL_RUN_GUIDE.md](../LOCAL_RUN_GUIDE.md)  
> - **Executive Summary:** [docs/submission/01_EXECUTIVE_SUMMARY.md](01_EXECUTIVE_SUMMARY.md)  
> - **Demo Day Script:** [docs/submission/05_DEMO_DAY_SCRIPT.md](05_DEMO_DAY_SCRIPT.md)  
>
> Thank you for your time and evaluation.

---

## Version C: Technical Reviewer & Code Judge Guide

*(Ideal for: Technical judges, staff engineers, open-source maintainers reviewing code)*

> **MedicalPlab — Technical Architecture & Code Audit Guide**
>
> Welcome! MedicalPlab is architected around the principle that **the generative model participates in learning, but does not become the source of medical truth.**
>
> **Fast Evaluation Steps (Clone & Run):**
> 1. Clone: `git clone https://github.com/AdhamElsayedAI/MedicalPlab.git && cd MedicalPlab`
> 2. Setup Python environment (Python 3.11 or 3.12):
>    ```bash
>    python -m venv .venv && source .venv/bin/activate  # (.venv\Scripts\Activate.ps1 on Windows)
>    pip install -r requirements.txt
>    ```
> 3. Bootstrap data & run release gate verifier:
>    ```bash
>    python Scripts/bootstrap_local_data.py
>    python Scripts/verify_local_release.py
>    ```
> 4. Start backend & frontend:
>    ```bash
>    # Terminal 1 (Backend - Bash/Linux):
>    MEDICALPLAB_RUNTIME_MODE=pilot uvicorn production_main:app --host 127.0.0.1 --port 8000
>    # Terminal 1 (Backend - Windows PowerShell):
>    # $env:MEDICALPLAB_RUNTIME_MODE="pilot"; uvicorn production_main:app --host 127.0.0.1 --port 8000
>
>    # Terminal 2 (Frontend):
>    cd frontend && npm install && npm run dev
>    ```
>
> **Key Architecture to Inspect:**
> - **Single Authoritative Pipeline:** `Adaptive Layer` $\rightarrow$ `TutorService` (`src/medicalplab/tutor/service.py`) $\rightarrow$ `Shared Evidence Engine`.
> - **Deterministic 3D Anatomy:** Check `src/medicalplab/anatomy/` and frontend Three.js scene controller; observe that raycast scoring is 100% deterministic against UBERON ontology IDs with zero AI mesh generation.
> - **OpenAPI Contract:** Run `python Scripts/verify_mobile_contract_drift.py` to confirm 0 drift across 43 paths and 44 operations.
> - **Security & Boundaries:** Check `SECURITY.md` and `tests/staging/test_staging_security.py` for fail-closed credential and endpoint boundaries.
>
> Complete technical documentation is indexed in [docs/submission/04_TECHNICAL_DIFFERENTIATORS.md](04_TECHNICAL_DIFFERENTIATORS.md).
