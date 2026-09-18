# MedicalPlab — Authoritative Local Run Guide
## Complete, Self-Contained Local Setup for Developers, Reviewers & Mobile Engineers

MedicalPlab is **local-first**. You can clone, configure, and run the entire product on your local workstation without any cloud account, payment card, external staging server, or paid LLM API key.

---

## 1. System Prerequisites

| Prerequisite | Recommended Version | Minimum Version | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | `3.11` or `3.12` | `3.11` | 64-bit Python (`pyproject.toml`: `>=3.11,<3.13`) |
| **Node.js** | `20 LTS` or `22 LTS` | `20.9.0` | Required for Next.js frontend (`engines: ">=20.9.0"`) |
| **npm** | `10+` | `9.0` | Bundled with Node.js |
| **OS** | Windows 10/11, macOS, or Linux | Any supported OS | Windows PowerShell prioritized |

> [!NOTE]
> **No GPU or Heavy ML Required.** MedicalPlab runs on standard CPU hardware. PyTorch, CUDA, Hugging Face transformers, and local 7B weights are NOT required for the standard local runtime (`GPU_REQUIRED = NO`).

---

## 2. Windows 10/11 Quick Start (PowerShell / VS Code)

### Automated Start (Fastest)
From the repository root in PowerShell:
```powershell
.\Scripts\start_local.ps1
```
*If script execution is restricted by Windows execution policy, run:*
```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\start_local.ps1
```

---

### Manual Step-by-Step Setup (Windows)

#### Step 1: Clone Repository
```powershell
git clone https://github.com/AdhamElsayedAI/MedicalPlab.git
cd MedicalPlab
```

#### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If using classic Command Prompt `cmd.exe`, run: `.\.venv\Scripts\activate.bat`)*

#### Step 3: Install Backend Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Configure Local Environment
Copy `.env.example` to `.env` (all defaults are safe, zero-cost, and require zero secrets):
```powershell
Copy-Item .env.example .env
```
Or set environment variables in your active shell:
```powershell
$env:PYTHONPATH = "src;."
$env:MEDICALPLAB_RUNTIME_MODE = "pilot"
$env:MEDICALPLAB_PLAB_PREVIEW_QA = "1"
$env:MEDICALPLAB_PHASE_2B_ENABLED = "1"
$env:MEDICALPLAB_ANATOMY_3D_ENABLED = "1"
$env:MEDICALPLAB_TUTOR_PROVIDER = "stub"
$env:MEDICALPLAB_STAGING_GATE_ENABLED = "0"
$env:ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
$env:PORT = "8000"
```

#### Step 5: Start FastAPI Backend
```powershell
uvicorn production_main:app --host 127.0.0.1 --port 8000
```
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Readiness & Manifest: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)
- Interactive API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Step 6: Start Next.js Frontend (in a second terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open your browser to: **[http://localhost:3000](http://localhost:3000)**

---

## 3. Linux / macOS Quick Start

### Automated Start
```bash
chmod +x ./Scripts/start_local.sh
./Scripts/start_local.sh
```

### Manual Setup
```bash
git clone https://github.com/AdhamElsayedAI/MedicalPlab.git
cd MedicalPlab

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env

export PYTHONPATH="src:."
export MEDICALPLAB_RUNTIME_MODE="pilot"
export MEDICALPLAB_PLAB_PREVIEW_QA="1"
export MEDICALPLAB_PHASE_2B_ENABLED="1"
export MEDICALPLAB_ANATOMY_3D_ENABLED="1"
export MEDICALPLAB_TUTOR_PROVIDER="stub"
export MEDICALPLAB_STAGING_GATE_ENABLED="0"
export ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
export PORT="8000"

uvicorn production_main:app --host 127.0.0.1 --port 8000
```

---

## 4. Mobile App Integration (Local Development)

Mobile developers (Flutter, React Native, iOS, Android) connect directly to the local backend:

| Client Environment | Target Base URL | Notes |
| :--- | :--- | :--- |
| **iOS Simulator** | `http://127.0.0.1:8000` | Loopback shares host network directly |
| **Android Emulator** | `http://10.0.2.2:8000` | Special 10.0.2.2 alias maps to host loopback `127.0.0.1` |
| **Physical Phone (LAN)** | `http://<YOUR_PC_LAN_IP>:8000` | Run backend with `--host 0.0.0.0` (e.g. `http://192.168.1.15:8000`) |

### Mobile Headers
- `X-User-Id`: Supply any synthetic student identifier (e.g. `learner_mobile_001`) for state partitioning.
- `X-Staging-Key`: **NOT REQUIRED** for local development (`LOCAL_RUN_REQUIRES_STAGING_KEY = NO`).

### Physical Device LAN Binding
When connecting a physical smartphone over local Wi-Fi:
1. Start backend binding to all interfaces:
   ```powershell
   uvicorn production_main:app --host 0.0.0.0 --port 8000
   ```
2. Find your local IPv4 address via `ipconfig` (Windows) or `ifconfig` (macOS/Linux).
3. Ensure Windows Defender Firewall allows inbound connections on TCP port 8000.

---

## 5. Postman Local Suite Execution

MedicalPlab includes a complete pre-configured Postman test environment:

1. Open Postman.
2. Import Collection: [`docs/mobile-handoff/MedicalPlab.mobile.postman_collection.json`](./mobile-handoff/MedicalPlab.mobile.postman_collection.json)
3. Import Environment: [`docs/mobile-handoff/MedicalPlab_Local.postman_environment.json`](./mobile-handoff/MedicalPlab_Local.postman_environment.json)
4. Select environment **MedicalPlab Local** (`base_url = http://127.0.0.1:8000`).
5. Run collection — all 12 mobile contract endpoints execute successfully out-of-the-box.

---

## 6. Optional Docker Path

Docker is completely optional. If Docker is installed on your machine and you prefer a containerized runtime:

```bash
# Build the multi-stage production image (approx. 271 MB)
docker build -t medicalplab-api:local .

# Run container locally with safe defaults
docker run -p 8000:8080 \
  -e MEDICALPLAB_RUNTIME_MODE=pilot \
  -e MEDICALPLAB_PLAB_PREVIEW_QA=1 \
  -e MEDICALPLAB_PHASE_2B_ENABLED=1 \
  -e MEDICALPLAB_ANATOMY_3D_ENABLED=1 \
  -e MEDICALPLAB_TUTOR_PROVIDER=stub \
  -e MEDICALPLAB_STAGING_GATE_ENABLED=0 \
  -e PORT=8080 \
  medicalplab-api:local
```
Access at [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

---

## 7. Troubleshooting Guide

### 1. PowerShell Execution Policy Restriction
- **Symptom:** `.\.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.`
- **Fix:** In your current terminal session, run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
  Then reactivate: `.\.venv\Scripts\Activate.ps1`.

### 2. Port Already in Use (Error: [Errno 10048] address already in use)
- **Symptom:** Uvicorn fails to start because port 8000 is occupied.
- **Fix (Windows):** Find and terminate the process holding port 8000:
  ```powershell
  netstat -ano | findstr :8000
  Stop-Process -Id <PID> -Force
  ```
  Or choose an alternative port:
  ```powershell
  uvicorn production_main:app --host 127.0.0.1 --port 8088
  ```

### 3. Node / npm Version Discrepancies
- **Symptom:** Next.js build errors or module resolution failures in `frontend/`.
- **Fix:** Ensure Node.js >=20.9 (recommended: 20 LTS or 22 LTS) is active:
  ```bash
  node -v
  npm -v
  cd frontend
  npm ci || npm install
  ```

### 4. Windows Firewall Blocking Mobile Device
- **Symptom:** Mobile device on Wi-Fi receives `Connection timed out` reaching `http://192.168.x.x:8000`.
- **Fix:** Add an inbound firewall rule for TCP port 8000:
  ```powershell
  New-NetFirewallRule -DisplayName "MedicalPlab Local API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
  ```

### 5. SQLite State Reset
- **Symptom:** Want to reset student progress to a clean state.
- **Fix:** Delete local SQLite databases under `Data/persistence/`:
  ```powershell
  Remove-Item -Force Data\persistence\*.sqlite3, Data\persistence\*.db -ErrorAction SilentlyContinue
  ```
  The backend will automatically regenerate fresh schemas upon startup.

### 6. Tutor Local Stub Behavior
- **Symptom:** Tutor responses state `[Deterministic Clinical Demonstration Provider]`.
- **Reason:** By default, MedicalPlab operates with `MEDICALPLAB_TUTOR_PROVIDER=stub` to ensure zero-cost, privacy-preserving, reproducible local execution without external API billing.
- **Optional Live LLM:** If you wish to enable live generation, set `MEDICALPLAB_TUTOR_PROVIDER=gemini` and export `GEMINI_API_KEY=your-key`.

---

## 8. Authoritative Safety & Capability Boundaries

1. **`MOBILE_PRODUCTION_AUTH_READY = NO`**  
   The `X-User-Id` header provides synthetic learner partitioning for demo and local integration testing. It is **NOT** cryptographic user authentication.
2. **`PLAB_PUBLIC_RELEASE_READY = NO`**  
   PLAB questions are candidates under clinician panel review. In standard production (`MEDICALPLAB_PLAB_PREVIEW_QA=0`), candidate items fail closed to 0 released items.
3. **`LOCAL_RUN_REQUIRES_CLOUD = NO`**  
   Cloud accounts, Google Cloud Run, and Render are NOT required for delivery or evaluation.
4. **`LOCAL_RUN_REQUIRES_PAYMENT = NO`**  
   $0 expected on all local flows. Zero paid infrastructure or credit cards needed.
