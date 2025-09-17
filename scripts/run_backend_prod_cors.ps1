# Runs the FastAPI backend with a production CORS allowlist.
# Usage:
#   .\scripts\run_backend_prod_cors.ps1 -AllowedOrigins "https://app.sunchaser.app,https://www.sunchaser.app"
param(
  [string]$AllowedOrigins = "https://app.sunchaser.app,https://www.sunchaser.app"
)

$env:CORS_ALLOWED_ORIGINS = $AllowedOrigins
$env:DEV_ALLOW_CORS = "false"
$env:CORS_ENFORCE = "true"

Write-Host "Starting backend with CORS allowlist: $AllowedOrigins"
python -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000
