<#
.SYNOPSIS
    MedicalPlab Authoritative Local Start Script (Windows PowerShell)

.DESCRIPTION
    Sets up a local Python virtual environment, installs runtime dependencies,
    configures safe zero-cost local defaults, and launches the MedicalPlab backend.

.EXAMPLE
    .\Scripts\start_local.ps1
    powershell -ExecutionPolicy Bypass -File .\Scripts\start_local.ps1
#>

[CmdletBinding()]
param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location -Path $ProjectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       MedicalPlab — Local-First Quick Start (Windows)      " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray

# 1. Verify Python Installation
Write-Host "`n[1/5] Checking Python prerequisite..." -ForegroundColor Yellow
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
    if (-not $PythonCmd) {
        Write-Error "ERROR: MedicalPlab currently supports Python 3.11 and 3.12. Python was not found on PATH. Please install Python 3.11 or 3.12 from https://www.python.org."
        exit 1
    }
}

$PythonVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Detected Python version: $PythonVersion" -ForegroundColor Green
$Major, $Minor = $PythonVersion.Split('.')
if ([int]$Major -ne 3 -or ([int]$Minor -ne 11 -and [int]$Minor -ne 12)) {
    Write-Error "ERROR: MedicalPlab currently supports Python 3.11 and 3.12 (found $PythonVersion)."
    exit 1
}

# 2. Virtual Environment Setup
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

Write-Host "`n[2/5] Configuring virtual environment (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating fresh virtual environment in .venv..." -ForegroundColor Gray
    & python -m venv $VenvDir
    if (-not (Test-Path $VenvPython)) {
        Write-Error "ERROR: Failed to create virtual environment at $VenvDir."
        exit 1
    }
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "Existing virtual environment found." -ForegroundColor Green
}

# 3. Dependency Installation
if (-not $SkipInstall) {
    Write-Host "`n[3/5] Verifying and installing runtime dependencies..." -ForegroundColor Yellow
    & "$VenvPython" -m pip install --upgrade pip --quiet
    & "$VenvPython" -m pip install -r (Join-Path $ProjectRoot "requirements.txt") --quiet
    Write-Host "Dependencies verified." -ForegroundColor Green
} else {
    Write-Host "`n[3/5] Skipping dependency installation (-SkipInstall)." -ForegroundColor Gray
}

# 3.5 Bootstrap public-safe local data assets (CC BY 4.0 validation fixtures)
& "$VenvPython" (Join-Path $ProjectRoot "Scripts\bootstrap_local_data.py")

# 4. Safe Local Environment Configuration (Zero Secrets, Zero Paid Services)
Write-Host "`n[4/5] Applying safe local environment defaults..." -ForegroundColor Yellow
$env:PYTHONPATH = "$ProjectRoot;$ProjectRoot\src"
$env:MEDICALPLAB_RUNTIME_MODE = "pilot"
$env:MEDICALPLAB_PLAB_PREVIEW_QA = "1"
$env:MEDICALPLAB_PHASE_2B_ENABLED = "1"
$env:MEDICALPLAB_ANATOMY_3D_ENABLED = "1"
$env:MEDICALPLAB_TUTOR_PROVIDER = "stub"
$env:MEDICALPLAB_STAGING_GATE_ENABLED = "0"
$env:ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
$env:PORT = "$Port"

Write-Host "  - Runtime Mode:        pilot (strict clinical rules)" -ForegroundColor DarkGray
Write-Host "  - PLAB Preview QA:     enabled (36 review questions)" -ForegroundColor DarkGray
Write-Host "  - Socratic Remediation: enabled (Phase 2B)" -ForegroundColor DarkGray
Write-Host "  - 3D Anatomy Lab:      enabled" -ForegroundColor DarkGray
Write-Host "  - Tutor Provider:      stub (zero-cost deterministic)" -ForegroundColor DarkGray
Write-Host "  - Staging Access Gate: disabled (direct local access)" -ForegroundColor DarkGray

# 5. Launch Backend Server
Write-Host "`n[5/5] Launching MedicalPlab Backend..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "  Backend Service URL:   http://$HostAddress`:$Port" -ForegroundColor Green
Write-Host "  Health Check:          http://$HostAddress`:$Port/health" -ForegroundColor Green
Write-Host "  Readiness & Manifest:  http://$HostAddress`:$Port/ready" -ForegroundColor Green
Write-Host "  API Documentation:     http://$HostAddress`:$Port/docs" -ForegroundColor Green
Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "To launch the Next.js frontend in another terminal:" -ForegroundColor Magenta
Write-Host "  cd frontend" -ForegroundColor Gray
Write-Host "  npm install" -ForegroundColor Gray
Write-Host "  npm run dev" -ForegroundColor Gray
Write-Host "  Open: http://localhost:3000" -ForegroundColor Gray
Write-Host "------------------------------------------------------------`n" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the backend server.`n" -ForegroundColor DarkYellow

& "$VenvPython" -m uvicorn production_main:app --host $HostAddress --port $Port
