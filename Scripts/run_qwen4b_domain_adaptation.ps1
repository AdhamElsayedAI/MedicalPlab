#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot | Split-Path -Parent
$RenalEnv = Join-Path $Root ".renal_env"
$QwenEnv = Join-Path $Root ".qwen4b_env"
$Src = Join-Path $Root "src"
New-Item -ItemType Directory -Force -Path $QwenEnv | Out-Null
$env:PYTHONPATH = "$QwenEnv;$RenalEnv;$Src"

# Preserve the repository's proven Python 3.12 GPU convention; never install/replace torch here.
try { & py -3.12 -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 85)" }
catch { Write-Host "CUDA_NOT_AVAILABLE"; exit 85 }
if ($LASTEXITCODE -ne 0) { Write-Host "CUDA_NOT_AVAILABLE"; exit 85 }

# Install only adaptation-layer packages into an isolated target when missing. CUDA torch is never replaced.
$Required = [ordered]@{
    "peft" = "peft>=0.17,<1"
    "accelerate" = "accelerate>=1.2,<2"
    "bitsandbytes" = "bitsandbytes>=0.46,<1"
    "psutil" = "psutil>=6,<8"
    "safetensors" = "safetensors>=0.5,<1"
}
foreach ($ImportName in $Required.Keys) {
    & py -3.12 -c "import $ImportName" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $Spec = $Required[$ImportName]
        Write-Host "Installing missing adaptation dependency: $Spec"
        & py -3.12 -m pip install --disable-pip-version-check --target $QwenEnv --upgrade --no-deps $Spec
        if ($LASTEXITCODE -ne 0) { throw "DEPENDENCY_INSTALL_FAILED: $Spec" }
    }
}

Set-Location $Root
& py -3.12 (Join-Path $Root "Scripts\run_qwen4b_domain_adaptation.py")
exit $LASTEXITCODE
