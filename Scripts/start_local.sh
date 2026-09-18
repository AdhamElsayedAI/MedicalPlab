#!/usr/bin/env bash
# ==============================================================================
# MedicalPlab Authoritative Local Start Script (Linux / macOS)
# ==============================================================================
# Sets up a local Python virtual environment, installs runtime dependencies,
# configures safe zero-cost local defaults, and launches the MedicalPlab backend.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

HOST_ADDR="${1:-127.0.0.1}"
PORT="${2:-8000}"

echo "============================================================"
echo "       MedicalPlab — Local-First Quick Start (Unix)        "
echo "============================================================"
echo "Project Root: $PROJECT_ROOT"

# 1. Verify Python Installation
echo -e "\n[1/5] Checking Python prerequisite..."
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3.10+ is required but not found on PATH." >&2
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Detected Python version: $PYTHON_VERSION"

# 2. Virtual Environment Setup
VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

echo -e "\n[2/5] Configuring virtual environment (.venv)..."
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Creating fresh virtual environment in .venv..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "Virtual environment created."
else
    echo "Existing virtual environment found."
fi

# 3. Dependency Installation
echo -e "\n[3/5] Verifying and installing runtime dependencies..."
"$VENV_PYTHON" -m pip install --upgrade pip --quiet
"$VENV_PYTHON" -m pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
echo "Dependencies verified."

# 3.5 Bootstrap public-safe local data assets (CC BY 4.0 validation fixtures)
"$VENV_PYTHON" "$PROJECT_ROOT/Scripts/bootstrap_local_data.py"

# 4. Safe Local Environment Configuration (Zero Secrets, Zero Paid Services)
echo -e "\n[4/5] Applying safe local environment defaults..."
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src"
export MEDICALPLAB_RUNTIME_MODE="pilot"
export MEDICALPLAB_PLAB_PREVIEW_QA="1"
export MEDICALPLAB_PHASE_2B_ENABLED="1"
export MEDICALPLAB_ANATOMY_3D_ENABLED="1"
export MEDICALPLAB_TUTOR_PROVIDER="stub"
export MEDICALPLAB_STAGING_GATE_ENABLED="0"
export ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
export PORT="$PORT"

echo "  - Runtime Mode:        pilot (strict clinical rules)"
echo "  - PLAB Preview QA:     enabled (36 review questions)"
echo "  - Socratic Remediation: enabled (Phase 2B)"
echo "  - 3D Anatomy Lab:      enabled"
echo "  - Tutor Provider:      stub (zero-cost deterministic)"
echo "  - Staging Access Gate: disabled (direct local access)"

# 5. Launch Backend Server
echo -e "\n[5/5] Launching MedicalPlab Backend..."
echo "------------------------------------------------------------"
echo "  Backend Service URL:   http://$HOST_ADDR:$PORT"
echo "  Health Check:          http://$HOST_ADDR:$PORT/health"
echo "  Readiness & Manifest:  http://$HOST_ADDR:$PORT/ready"
echo "  API Documentation:     http://$HOST_ADDR:$PORT/docs"
echo "------------------------------------------------------------"
echo "To launch the Next.js frontend in another terminal:"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"
echo "  Open: http://localhost:3000"
echo "------------------------------------------------------------"
echo "Press Ctrl+C to stop the backend server."
echo ""

exec "$VENV_PYTHON" -m uvicorn production_main:app --host "$HOST_ADDR" --port "$PORT"
