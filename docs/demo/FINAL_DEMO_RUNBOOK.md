# MedicalPlab — Final Product Demo Runbook
**End-to-End Walkthrough Guide for Mentors, Judges, Teammates, and Mobile Developers**

---

## 1. Overview & Architecture Stance

MedicalPlab is a clinical edtech platform demonstrating closed-loop adaptive medical learning:
```
Attempt → Reasoning Signal → Adaptive Intervention → Socratic Support → Independent Transfer → Evidence-Grounded Tutor → Spatial 3D Learning → Unified Progress
```
This runbook enables any team member to start and reliably conduct a live 2–4 minute presentation of the authoritative application without contacting backend engineers.

---

## 2. Pre-Requisites & System Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** 3.11 or 3.12 (with virtualenv activated)
- **Node.js:** v20.x or v22.x+ (npm 10+)
- **Browser:** Google Chrome or Microsoft Edge (modern Chromium-based)
- **Port Availability:**
  - `8000`: MedicalPlab FastApi backend
  - `3000`: MedicalPlab Next.js production frontend

---

## 3. Authoritative Service Startup

Open two terminal windows in `C:\Users\Adham Elsayed\Desktop\AdhamElsayedAI\MedicalPlab` (or repo root):

### Terminal 1: Authoritative Backend (Preview QA Enabled)

```powershell
# Windows PowerShell
$env:PYTHONPATH="src;."
$env:MEDICALPLAB_RUNTIME_MODE="pilot"
$env:MEDICALPLAB_PLAB_PREVIEW_QA="1"
$env:MEDICALPLAB_PHASE_2B_ENABLED="1"
$env:MEDICALPLAB_ANATOMY_3D_ENABLED="1"
$env:ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

python -m uvicorn production_main:app --host 127.0.0.1 --port 8000 --workers 1
```

```bash
# macOS / Linux Bash
export PYTHONPATH="src:."
export MEDICALPLAB_RUNTIME_MODE="pilot"
export MEDICALPLAB_PLAB_PREVIEW_QA="1"
export MEDICALPLAB_PHASE_2B_ENABLED="1"
export MEDICALPLAB_ANATOMY_3D_ENABLED="1"
export ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

python -m uvicorn production_main:app --host 127.0.0.1 --port 8000 --workers 1
```

### Terminal 2: Production Frontend

```bash
cd frontend
npm run build
npm run start -- -p 3000
```

---

## 4. Verification & Health Checks

Before presenting, verify both services respond:

1. **Backend Health:**
   ```bash
   curl http://127.0.0.1:8000/health
   # Expected: {"status":"healthy","runtime_mode":"pilot","evidence_engine":"shared","rag_corpus":"pmc_open_access"}
   ```
2. **Backend Readiness:**
   ```bash
   curl http://127.0.0.1:8000/ready
   # Expected: {"status":"ready","database":"connected","evidence_index":"ready","anatomy_assets":"ready"}
   ```
3. **Frontend Availability:**
   Open `http://localhost:3000` in Chrome. You should see the dark-mode clinical hero interface with active ambient particles and system badges.

---

## 5. Demo Reset Procedure (Fresh Synthetic Identity)

**DO NOT delete database files or run git reset to reset learner state.**
MedicalPlab uses synthetic user scoping via the `X-User-Id` HTTP header and browser `localStorage`.

### Resetting in Browser:

1. Open DevTools Console (F12 or Ctrl+Shift+I) on `http://localhost:3000`.
2. Generate and set a fresh demo learner ID:
   ```javascript
   const freshId = "mentor_demo_" + Date.now().toString(36);
   localStorage.setItem("medicalplab.university.learner.v1", freshId);
   localStorage.setItem("medicalplab.authoritative_learner_id.v1", freshId);
   console.log("Initialized fresh demo learner:", freshId);
   location.reload();
   ```
3. The demo learner now starts from an absolute zero-state (clean mastery, no history, pristine adaptive engine state).

---

## 6. Exact Demo Journey Walkthrough (2–4 Minutes)

Follow this precise sequence for a smooth, high-impact demonstration:

### Step 1: Home / Learning Hub (`0:00 – 0:30`)
- **URL:** `http://localhost:3000/`
- **Showcase:**
  - Ambient particle motion & Cognitive Loop animation (Attempt → Reasoning Signal → Socratic Remediation → Transfer).
  - Runtime truth badges: University items (6 Preclinical), PLAB status ("36 Preview QA Candidates"), 3D Anatomy status.
  - Clear governance disclaimer: explicitly states "Preview QA" and separates roadmap items from current pilot capabilities.
- **Narrative:** *"MedicalPlab is not just another question bank that tells students whether they got an answer right or wrong. It acts as an adaptive clinical intelligence system that diagnoses learner reasoning and intervenes at the conceptual level."*

### Step 2: University Preclinical Practice (`0:30 – 1:00`)
- **URL:** `http://localhost:3000/university`
- **Action:**
  - Click **Renal Physiology** subject → Click **RAAS Mechanisms** topic.
  - Question `UNI-RENAL-001`: *"A 45-year-old male with hypertension... What is the primary substrate upon which active renin acts?"*
  - Select **Option B: Angiotensin II** (the clinical distractor representing confusion of enzyme substrate with downstream product).
  - Click **Check Answer**.
- **Showcase:**
  - Immediate distractor analysis explaining *why* Angiotensin II is incorrect (Ang I is cleaved by ACE to Ang II, whereas renin cleaves angiotensinogen).
  - Adaptive Intervention banner prompts: *"Reasoning pattern signal detected: Substrate vs downstream product confusion. Socratic Remediation Available."*
- **Narrative:** *"Notice the platform didn't just flash a red box. It recognized the student confused the enzyme's substrate with downstream cleavage products. It offers immediate Socratic scaffolding."*

### Step 3: Socratic Remediation & Held-out Transfer (`1:00 – 2:00`)
- **Action:**
  - Click **Launch Socratic Remediation**.
  - **Turn 1 (Probe):** The AI asks: *"What does active renin cleave directly to initiate this cascade?"*
    - Type: *"Renin acts on an upstream precursor protein produced by the liver."*
    - Click **Submit Reasoning**.
  - **Turn 2 (Guide):** AI affirms hepatic origin and guides to nomenclature.
    - Type: *"It cleaves angiotensinogen into angiotensin I."*
    - Click **Submit Reasoning**.
  - **Turn 3 / Transfer (Consolidate & Transfer):** The AI presents a **held-out transfer question** (`UNI-RENAL-001-T`):
    - Question tests transfer of the concept under novel clinical phrasing.
    - Select **Option A: Angiotensinogen**.
    - Click **Submit Transfer Assessment**.
- **Showcase:**
  - Remediation successfully marked **Mastered / Closed Loop**.
  - Held-out transfer item scored deterministically by backend.
  - Zero pre-answer leakage of the correct option or explanation.
- **Narrative:** *"The learner wasn't just handed the answer. They worked through the reasoning steps socratically and proved conceptual transfer on an unseen item."*

### Step 4: Evidence-Grounded AI Tutor (`2:00 – 2:45`)
- **URL:** `http://localhost:3000/tutor`
- **Action:**
  - In the prompt field, ask: *"How does RAAS increase blood pressure?"*
  - Click **Inquire**.
- **Showcase:**
  - Status badge: **Evidence-Grounded / SUPPORTED**.
  - Click **Expand Citations** to view exact PMC open-access document ID (`DOC-PMC-RENAL-0001:C001`), chunk ID, and license metadata.
  - Mention Safety Guard: If an ungrounded or out-of-scope query is entered (e.g. general non-renal queries), the tutor immediately transitions to **SAFE_FALLBACK** with zero hallucinated clinical claims and zero fake citations.
- **Narrative:** *"Every medical assertion generated by our AI Tutor is verified proposition-by-proposition against authoritative open-access evidence before being rendered."*

### Step 5: 3D Spatial Anatomy (`2:45 – 3:30`)
- **URL:** `http://localhost:3000/anatomy`
- **Action:**
  - Guided Task: Click **Left Renal Vein** structure → observe 3D spatial zoom and physiological correlation (receives left gonadal and suprarenal drainage).
  - Challenge Mode: Switch to **Challenge** tab → Locate and select **Left Renal Artery** → Click **Check Answer**.
- **Showcase:**
  - Interactive WebGL/Three.js spatial organ model.
  - Deterministic backend challenge scoring (`/api/v1/anatomy/challenge/verify`).
- **Narrative:** *"To anchor preclinical biochemistry and pharmacology, MedicalPlab integrates spatial 3D organ anatomy with deterministic structural challenges scored on the backend."*

### Step 6: Unified Progress & PLAB Preview QA (`3:30 – 4:00`)
- **URL:** `http://localhost:3000/progress`
  - Show how the University attempt, Socratic remediation, and 3D challenge are unified in real time under the demo learner ID.
- **URL:** `http://localhost:3000/practice`
  - Navigate to **PLAB Candidate Bank**.
  - Point out the clear **Preview QA Governance Banner** (36 candidates in review; zero golden production release claims).
  - Explain the fail-closed clinical governance: if `MEDICALPLAB_PLAB_PREVIEW_QA=0`, the API returns `GOLDEN_ONLY` (0 released), preventing unreviewed clinical items from ever reaching learners.

---

## 7. Demo Timing Summary

| Phase | Screen / Feature | Target Duration | Key Wow Factor |
|---|---|---|---|
| 1 | Home / Learning Hub | 30 sec | Cognitive Loop animation, clinical styling, system badges |
| 2 | University Practice | 30 sec | Reasoning-pattern distractor capture without leakage |
| 3 | Socratic Remediation & Transfer | 60 sec | True 3-turn socratic dialogue & held-out transfer mastery |
| 4 | Evidence-Grounded Tutor | 45 sec | Real PMC citations, license provenance, SAFE_FALLBACK guard |
| 5 | 3D Spatial Anatomy | 45 sec | Interactive 3D spatial model & backend-verified challenge |
| 6 | Unified Progress & PLAB Preview | 30 sec | Unified telemetry & strict fail-closed clinical governance |
| **Total** | **Full Walkthrough** | **~3 min 40 sec** | **Coherent, end-to-end adaptive clinical intelligence** |
