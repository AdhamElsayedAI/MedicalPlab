#!/usr/bin/env bash
# MedicalPlab - Google Cloud Run Automated Deployment Script (Bash / Cloud Shell)
set -euo pipefail

REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-medicalplab-api}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"

echo "================================================="
echo " MedicalPlab API - Google Cloud Run Deployment  "
echo "================================================="

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    read -rp "Enter your Google Cloud Project ID: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

echo "Target Project: $PROJECT_ID"
echo "Target Region:  $REGION"
echo "Service Name:   $SERVICE_NAME"

echo ""
echo "[1/3] Enabling required Google Cloud APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project "$PROJECT_ID"

echo ""
echo "[2/3] Building container and deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars ALLOWED_ORIGINS="https://medical-plab.vercel.app" \
    --project "$PROJECT_ID"

echo ""
echo "[3/3] Retrieving Service URL..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --format "value(status.url)" --project "$PROJECT_ID")

echo "================================================="
echo " Deployment Successful!"
echo " Backend Production URL: $SERVICE_URL"
echo " Health Endpoint:       $SERVICE_URL/health"
echo " Interactive Docs:      $SERVICE_URL/docs"
echo "================================================="
echo ""
echo "Next Step: Set NEXT_PUBLIC_API_URL in Vercel to: $SERVICE_URL"
