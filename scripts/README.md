Seed scripts

seed_forecasts.ps1 - PowerShell helper to run the backend fetch job and persist snapshots (JSON + SQLite).

Usage (PowerShell):

    .\scripts\seed_forecasts.ps1

This will attempt to activate `./.venv` if present and then run `Backend/scripts/fetch_forecasts.py` which writes `Backend/data/forecast_snapshot.json` and `Backend/data/forecast_snapshot.db`.
