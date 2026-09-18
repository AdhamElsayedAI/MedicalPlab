# MedicalPlab — Mentor & Reviewer Local Evaluation Runbook
**Target Audience:** Evaluators, Mentors, Technical Judges  
**Estimated Setup Time:** ~3 minutes  
**Cloud / External Account Requirement:** **NONE** ($0, zero cloud accounts, zero payment cards)  
**System Prerequisites:** Python 3.11 or 3.12; Node.js >=20.9 (recommended: 20 LTS or 22 LTS)  

---

## 1. Fast Track (5 Steps to Running App)

### Step 1: Clone Repository
```powershell
git clone https://github.com/AdhamElsayedAI/MedicalPlab.git
cd MedicalPlab
```

### Step 2: Launch Backend (Automated)
In PowerShell *(requires Python 3.11 or 3.12)*:
```powershell
.\Scripts\start_local.ps1
```
*(On Linux/macOS: `./Scripts/start_local.sh`)*

Wait ~15 seconds until the server prints:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 3: Launch Frontend
In a **second** terminal window *(requires Node.js >=20.9, recommended: 20 LTS or 22 LTS)*:
```powershell
cd MedicalPlab\frontend
npm install
npm run dev
```

### Step 4: Open in Browser
Navigate to: **[http://localhost:3000](http://localhost:3000)**

---

## 2. Recommended 3-Minute Evaluation Walkthrough

Follow this sequence to observe the full adaptive cognitive loop:

1. **Preclinical Assessment:**
   - Select subject: **Renal Physiology** &rarr; topic: **Glomerular Filtration & Hemodynamics**.
   - Review the question on GFR response to efferent arteriolar vasoconstriction.
   - Select option **B** (Effortful distractor representing efferent-afferent inversion).
   - Click **Submit Answer**. Instant deterministic feedback detects the cognitive distractor signal.

2. **Adaptive Socratic Remediation:**
   - The system automatically triggers the Socratic remediation loop (Turn 1: Cognitive Probe).
   - Read the preceptor probe asking to trace hydraulic pressure across the glomerular capillary bed.
   - Reply: *"Constricting the outflow pipe increases upstream hydrostatic pressure."*
   - Turn 2 guides your synthesis, and Turn 3 consolidates the physiological principle.

3. **Independent Held-Out Transfer Assessment:**
   - Click **Take Transfer Challenge**.
   - Notice the system presents a **new, unprompted clinical vignette** (`UNI-RENAL-001-T`) rather than blindly awarding mastery.
   - Answer: **A — Angiotensinogen**.
   - Transfer is confirmed deterministically.

4. **3D Spatial Anatomy Lab:**
   - Click **3D Anatomy Lab** in the navigation.
   - Interact with the HuBMAP CCF renal model in real-time.
   - Take the guided anatomical tour (`renal_vein_left`).
   - Complete the spatial structure identification challenge (`renal_artery_left`).

5. **Unified Learner Progress:**
   - Click **My Progress**.
   - Observe unified telemetry across Preclinical, Remediation, Tutor, and 3D Anatomy challenges.

---

## 3. Key Local Endpoints Reference

| Service | Local URL | Purpose |
| :--- | :--- | :--- |
| **Frontend Web UI** | [http://localhost:3000](http://localhost:3000) | Complete student learning interface |
| **Backend API Health** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | System health probe (returns HTTP 200) |
| **Readiness & Manifest** | [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready) | Manifest verification & mode inspection |
| **Interactive OpenAPI Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI for interactive exploration |

---

## 4. Expected Baseline & Known Invariants

- **Zero Paid LLM Tokens Required:** The local engine defaults to `MEDICALPLAB_TUTOR_PROVIDER=stub` providing instant, deterministic, zero-cost pedagogical responses.
- **Local Staging Gate Disabled:** Local developers do not need `X-Staging-Key` headers (`MEDICALPLAB_STAGING_GATE_ENABLED=0`).
- **Synthetic Learner Identity:** `X-User-Id` partitions demo learner state locally (`MOBILE_PRODUCTION_AUTH_READY = NO`).
- **PLAB Governance:** 36 candidate questions are served under Preview QA for clinician review; 0 golden released items.
