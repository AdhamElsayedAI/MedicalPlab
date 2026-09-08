# MedicalPlab - Google Cloud Run Automated Deployment Script (PowerShell)
param (
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$ServiceName = "medicalplab-api"
)

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " MedicalPlab API - Google Cloud Run Deployment  " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Verify gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI is not installed." -ForegroundColor Red
    Write-Host "Install Google Cloud SDK from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Determine project ID
if (-not $ProjectId) {
    $ProjectId = (gcloud config get-value project 2>$null)
    if (-not $ProjectId -or $ProjectId -eq "(unset)") {
        Write-Host "No active GCP project found." -ForegroundColor Yellow
        $ProjectId = Read-Host "Please enter your Google Cloud Project ID"
        gcloud config set project $ProjectId
    }
}

Write-Host "Target Project: $ProjectId" -ForegroundColor Green
Write-Host "Target Region:  $Region" -ForegroundColor Green
Write-Host "Service Name:   $ServiceName" -ForegroundColor Green

# Enable required Google Cloud services
Write-Host "`n[1/3] Enabling required Google Cloud APIs (Cloud Run, Cloud Build, Artifact Registry)..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project $ProjectId

# Build and deploy directly from source
Write-Host "`n[2/3] Building container and deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --source . `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --timeout 300 `
    --set-env-vars ALLOWED_ORIGINS="https://medical-plab.vercel.app" `
    --project $ProjectId

# Retrieve Service URL
$ServiceUrl = (gcloud run services describe $ServiceName --platform managed --region $Region --format "value(status.url)" --project $ProjectId)

Write-Host "`n[3/3] Deployment Verification..." -ForegroundColor Yellow
Write-Host "=================================================" -ForegroundColor Green
Write-Host " Deployment Successful!                          " -ForegroundColor Green
Write-Host " Backend Production URL: $ServiceUrl             " -ForegroundColor Green
Write-Host " Health Endpoint:       $ServiceUrl/health       " -ForegroundColor Green
Write-Host " Interactive Docs:      $ServiceUrl/docs         " -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host "`nNext Step: Set NEXT_PUBLIC_API_URL in Vercel to: $ServiceUrl" -ForegroundColor Cyan
