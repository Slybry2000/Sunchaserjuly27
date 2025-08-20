# Seed forecasts PowerShell helper
# Usage: Open PowerShell in repo root and run:
#    .\scripts\seed_forecasts.ps1

# Activate venv if present
if (Test-Path -Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating .venv..."
    . .\.venv\Scripts\Activate.ps1
} else {
    Write-Host ".venv not found; ensure your virtual environment is activated or install dependencies first"
}

Write-Host "Running fetch_forecasts.py to write data/forecast_snapshot.json and data/forecast_snapshot.db"
python Backend\scripts\fetch_forecasts.py
