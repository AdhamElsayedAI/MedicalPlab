# MedicalPlab Judge & Demo Guide

## Quick Start in Under 3 Minutes

This guide walks hackathon judges and evaluators through running and verifying MedicalPlab locally.

---

## 1. Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.x or 20.x (optional for frontend UI; backend API includes full Swagger docs)
- **Git**: For repository verification

---

## 2. Environment Setup

### 2.1. Clone and Prepare Configuration
```bash
# Copy example environment configuration
cp .env.example .env

# Set up Python virtual environment (recommended)
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

---

## 3. Running the Backend API

Start the FastAPI application gateway:

```bash
python main.py
```
*The server will start at `http://localhost:8000`.*

### Interactive API Documentation
Open your browser and navigate to:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 4. Running the Next.js Frontend (Optional UI)

```bash
cd frontend
npm install
npm run dev
```
*The frontend web application will start at `http://localhost:3000`.*

---

## 5. Verification: Running the Automated Test Gates

MedicalPlab is backed by comprehensive automated test suites verifying evidence closure, cryptographic integrity, and clinical safety:

### Step 1: Verify PLAB V9 Final Evidence Closure
```bash
python -m pytest tests/plab/v9 -q
```
*Expected Output: `14 passed in ~0.15s`.*
*Verifies 36 questions, 12 grounded, 24 quarantined, 0 false support, character-exact span containment, and SHA-256 integrity.*

### Step 2: Verify the Complete PLAB Pipeline Suite
```bash
python -m pytest tests/plab -q
```
*Expected Output: `77 passed in ~2.7s`.*

### Step 3: Run the Full Platform Test Suite
```bash
python -m pytest -q
```
*Expected Output: `594 passed, 1 skipped, 12 subtests passed`.*

---

## 6. Key Demo Capabilities to Inspect

### Feature 1: Deterministic PLAB V9 Evidence Layer
- Open [`Data/questions/versions/cardiorespiratory_batch_1_final_closure_v9.json`](file:///Data/questions/versions/cardiorespiratory_batch_1_final_closure_v9.json).
- Inspect any of the 12 `source_grounded` questions (e.g., Question 1 on NICE Hypertension stepped care).
- Notice the character-level `exact_source_span`, guideline publication date, and atomic claim decomposition.
- Inspect any of the 24 `quarantined` questions (e.g., Question 2 on Atrial Fibrillation rate vs. rhythm control).
- Notice the explicit machine-readable blockers (`DISTRACTOR_AMBIGUITY`, `CURRENCY_OUTDATED`) preventing unsafe serving to students.

### Feature 2: Bayesian Knowledge Tracing (BKT) Adaptive Learning
- Query the adaptive learning engine (`src/medicalplab/stage_e/`).
- The system models student latent knowledge states across GMC MLA specialties, adjusting difficulty and scheduling reviews based on individual slip and guess parameters.

### Feature 3: Clinician Review Queue (Fail-Closed Governance)
- Examine `src/medicalplab/plab/v9/closure_validator.py`.
- Notice that even with 100% technical evidence closure, `clinician_approved` remains `0` until a verified GMC doctor explicitly signs off.
- The system never auto-promotes unvetted AI questions to Golden status.

### Feature 4: Interactive OSCE Simulation
- Test the clinical simulation engine (`src/medicalplab/stage_f/`).
- Evaluate turn-by-turn clinical reasoning, history-taking, and automated safety trap detection.
