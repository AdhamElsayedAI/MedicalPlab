#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Renal V2 GPU runner — uses Python 3.12 + .renal_env PYTHONPATH
.DESCRIPTION
    Wrapper for running Renal V2 GPU scripts (matrix, ablation, reranker)
    using the correct Python 3.12 interpreter with .renal_env on PYTHONPATH.

    Usage:
      .\Scripts\run_gpu.ps1 matrix          # Run 16-config embedding matrix
      .\Scripts\run_gpu.ps1 ablation        # Run retrieval ablation
      .\Scripts\run_gpu.ps1 reranker        # Run Stage B reranker diagnostic
      .\Scripts\run_gpu.ps1 matrix --smoke  # Smoke test (1 config)
#>
param(
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateSet("matrix", "ablation", "reranker", "smoke")]
    [string]$Script,
    [switch]$Smoke
)

$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot | Split-Path -Parent
$RenalEnv = Join-Path $Root ".renal_env"
$Src = Join-Path $Root "src"

# Python 3.12 executable
$Py312 = "py"
$Py312Args = @("-3.12")
try {
    $ver = & py -3.12 --version 2>&1
    Write-Host "Python 3.12 detected: $ver"
} catch {
    Write-Error "Python 3.12 not found via 'py -3.12'. Install Python 3.12 first."
    exit 1
}

# Script map
$ScriptMap = @{
    "matrix"   = Join-Path $Root "Scripts\run_renal_v2_matrix.py"
    "ablation" = Join-Path $Root "Scripts\run_renal_v2_ablation.py"
    "reranker" = Join-Path $Root "Scripts\run_renal_v2_reranker.py"
    "smoke"    = Join-Path $Root "Scripts\run_renal_v2_matrix.py"
}

$TargetScript = $ScriptMap[$Script]
if (-not (Test-Path $TargetScript)) {
    Write-Error "Script not found: $TargetScript"
    exit 1
}

# Build environment
$env:PYTHONPATH = "$RenalEnv;$Src"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"

Write-Host "============================================================"
Write-Host "RENAL V2 GPU RUNNER"
Write-Host "Script: $TargetScript"
Write-Host "PYTHONPATH: $($env:PYTHONPATH)"
Write-Host "============================================================"

$PyArgs = @("-3.12", $TargetScript)
if ($Script -eq "smoke" -or $Smoke) {
    $PyArgs += "--smoke"
}

Write-Host "Running: py $($PyArgs -join ' ')"
Write-Host ""

& py @PyArgs

$ExitCode = $LASTEXITCODE
Write-Host ""
Write-Host "Exit code: $ExitCode"
exit $ExitCode
