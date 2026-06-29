# AI Interview Platform - Google Cloud Deployment
# Frontend: Firebase Hosting | Backend: Cloud Run
#
# Prerequisites:
#   1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
#   2. Install Firebase CLI: npm install -g firebase-tools
#   3. Run: gcloud auth login
#   4. Run: firebase login

param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1",
    [string]$BackendService = "ai-interview-backend",
    [string]$FrontendSite = ""
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " AI Interview Platform - GCP Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if (-not $ProjectId) {
    $ProjectId = Read-Host "Enter your GCP Project ID"
}
if (-not $FrontendSite) {
    $FrontendSite = $ProjectId
}

Write-Host ""
Write-Host "Project:       $ProjectId" -ForegroundColor Yellow
Write-Host "Region:        $Region" -ForegroundColor Yellow
Write-Host "Backend:       $BackendService" -ForegroundColor Yellow
Write-Host "Frontend:      https://$FrontendSite.web.app" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Proceed? (y/n)"
if ($confirm -ne "y") { exit 0 }

# ── 1. Set project ──
Write-Host "`n[1/5] Setting GCP project..." -ForegroundColor Green
gcloud config set project $ProjectId

# ── 2. Enable APIs ──
Write-Host "[2/5] Enabling APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com firebase.googleapis.com

# ── 3. Get env vars ──
Write-Host "[3/5] Backend environment variables:" -ForegroundColor Green
$dbUrl      = Read-Host "  DATABASE_URL"
$openaiKey  = Read-Host "  OPENAI_API_KEY"
$jwtSecret  = Read-Host "  JWT_SECRET_KEY"
$encKey     = Read-Host "  FIELD_ENCRYPTION_KEY"

$envVars = "DATABASE_URL=$dbUrl,OPENAI_API_KEY=$openaiKey,JWT_SECRET_KEY=$jwtSecret,FIELD_ENCRYPTION_KEY=$encKey,PYTHONPATH=/app,PYTHONUNBUFFERED=1"

# ── 4. Deploy backend to Cloud Run ──
Write-Host "[4/5] Deploying backend to Cloud Run..." -ForegroundColor Green
gcloud run deploy $BackendService `
    --source ./backend `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --min-instances 0 `
    --max-instances 10 `
    --timeout 300 `
    --port 8000 `
    --set-env-vars $envVars

$BACKEND_URL = gcloud run services describe $BackendService --region $Region --format="value(status.url)"
Write-Host "  Backend: $BACKEND_URL" -ForegroundColor Green

# ── 5. Build & deploy frontend ──
Write-Host "[5/5] Building frontend..." -ForegroundColor Green
$env:VITE_API_URL = $BACKEND_URL

Push-Location frontend
npm run build
Pop-Location

# Set firebase project
@{ projects = @{ default = $ProjectId } } | ConvertTo-Json | Out-File -Encoding utf8 .firebaserc

Write-Host "Deploying to Firebase Hosting..." -ForegroundColor Green
firebase deploy --only hosting --project $ProjectId

# ── Done ──
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host " DEPLOYED!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Frontend: https://$FrontendSite.web.app" -ForegroundColor Yellow
Write-Host " Backend:  $BACKEND_URL" -ForegroundColor Yellow
