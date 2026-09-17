# MedicalPlab — Presentation Failure Recovery Guide
**Contingency & Rapid Diagnostic Procedures for Live Presentations**

---

## 1. Overview & Failure Philosophy

Live presentations can encounter unexpected local port locks, asset loading hiccups, or missing environment variables. This document outlines concrete symptoms, instant diagnoses, and tested recovery fallbacks to ensure zero presentation crashes.

---

## 2. Contingency Matrix

### Incident 1: Backend Process Fails to Start

- **Symptom:**
  Running `python -m uvicorn production_main:app ...` throws `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): address already in use`.
- **Quick Diagnosis:**
  A previous Python or uvicorn worker is still holding port 8000 in the background.
- **Rapid Recovery Procedure:**
  ```powershell
  # Windows PowerShell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
  # Restart authoritative backend:
  $env:PYTHONPATH="src;."; $env:MEDICALPLAB_RUNTIME_MODE="pilot"; $env:MEDICALPLAB_PLAB_PREVIEW_QA="1"; $env:MEDICALPLAB_PHASE_2B_ENABLED="1"; $env:MEDICALPLAB_ANATOMY_3D_ENABLED="1"; python -m uvicorn production_main:app --host 127.0.0.1 --port 8000 --workers 1
  ```
  ```bash
  # Linux / macOS
  lsof -ti:8000 | xargs kill -9
  PYTHONPATH="src:." MEDICALPLAB_RUNTIME_MODE="pilot" MEDICALPLAB_PLAB_PREVIEW_QA="1" python -m uvicorn production_main:app --host 127.0.0.1 --port 8000 --workers 1
  ```

---

### Incident 2: Frontend Process Fails to Start

- **Symptom:**
  `npm run start` or `npm run dev` fails with `Port 3000 is already in use`.
- **Quick Diagnosis:**
  An earlier Next.js process or test runner is occupying port 3000.
- **Rapid Recovery Procedure:**
  ```powershell
  # Windows PowerShell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
  cd frontend
  npm run start -- -p 3000
  ```
  ```bash
  # Linux / macOS
  lsof -ti:3000 | xargs kill -9
  cd frontend && npm run start -- -p 3000
  ```

---

### Incident 3: 3D Anatomy Model Asset Load Failure / WebGL Disabled

- **Symptom:**
  Navigating to `/anatomy` displays a black viewport or WebGL context error: *"WebGL not supported or disabled"*.
- **Quick Diagnosis:**
  Hardware acceleration is disabled in Chrome flags or GPU process crashed.
- **Rapid Recovery Procedure:**
  1. Navigate to `chrome://settings/system` in Google Chrome and ensure **"Use graphics acceleration when available"** is turned ON.
  2. If on a remote terminal without a GPU, open Chrome with:
     ```bash
     chrome.exe --enable-webgl --ignore-gpu-blocklist
     ```
  3. **Safe Fallback Presentation Narrative:** If WebGL is strictly unavailable on the presenter's hardware, demonstrate the deterministic challenge logic via the API contract or show the certified screenshot pack (`docs/demo/final-showcase/06-anatomy-guided.png` & `07-anatomy-challenge.png`). Explain that 3D rendering uses standard GLTF/Three.js with backend challenge verification.

---

### Incident 4: Tutor Generative Provider Timeout or Offline

- **Symptom:**
  Asking a question in `/tutor` takes >10 seconds or logs a provider network error.
- **Quick Diagnosis:**
  Upstream generative API rate limits or network outage.
- **Safe Fallback Design (Automated):**
  MedicalPlab’s TutorService is architected with **automatic fail-closed fallbacks**.
  - If the provider times out or throws an error, the backend immediately serves a **SAFE_FALLBACK** response.
  - The UI displays an amber advisory badge: *"SAFE_FALLBACK applied — zero ungrounded clinical claims permitted."*
  - **Presenter Talking Point:** *"This highlights our safety governance in action! Rather than hallucinating plausible-sounding clinical advice when an upstream model is uncertain or unresponsive, MedicalPlab fails closed, presenting verified non-factual pedagogical guidance only."*

---

### Incident 5: Internet Unavailable (Offline Demo Environment)

- **Symptom:**
  Demo must be performed in an auditorium, conference room, or airplane with zero Wi-Fi.
- **Quick Diagnosis:**
  Local machine has no internet connectivity.
- **Safe Operation Mode:**
  MedicalPlab is **fully functional locally**:
  - The University Question Bank (`UNI-RENAL-001` through `006`), Socratic Remediation trees, held-out transfer items, and Adaptive state are stored locally in the repo (`Data/preclinical/` & SQLite memory).
  - The 3D Anatomy GLTF model assets are stored locally in `frontend/public/anatomy/`.
  - The shared evidence engine retrieval index is stored locally in `Data/evidence/`.
  - The stub tutor fallback provider operates completely offline.
  - *Known Limitation:* Online live Gemini calls will gracefully fail to local deterministic stub responses. Zero crash occurs.

---

### Incident 6: PLAB Preview Flag Omitted (`MEDICALPLAB_PLAB_PREVIEW_QA` not set)

- **Symptom:**
  Navigating to `/practice` shows **0 Questions Available** in the PLAB bank.
- **Quick Diagnosis:**
  The backend was started with `MEDICALPLAB_PLAB_PREVIEW_QA=0` (or unset), activating strict clinical fail-closed protection where only peer-reviewed golden questions are exposed.
- **Rapid Recovery Procedure:**
  1. **Option A (Demonstrate Production Governance):** Use this as an intentional demonstration moment!
     - Narrative: *"Notice the PLAB bank is currently empty in strict production mode. That is because MedicalPlab refuses to expose unreviewed candidate questions to learners until a clinician panel has signed off."*
  2. **Option B (Enable Candidate Preview):**
     - Stop backend (Ctrl+C).
     - Set `$env:MEDICALPLAB_PLAB_PREVIEW_QA="1"` and restart backend.
     - Refresh `/practice` — all 36 candidates are now accessible under the Preview QA banner.
