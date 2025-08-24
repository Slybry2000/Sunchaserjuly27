Development runbook

This file documents common environment flags and quick dev commands to run the backend and smoke checks locally (PowerShell examples).

Key env flags

- `ENABLE_Q` — Enable the typed `?q=` geocode path on `/recommend`. Default: `false`. Set to `true` to allow text queries in dev/staging.
- `DEV_ALLOW_GEOCODE` — Enable developer fallback geocoding (a few hard-coded mappings) when `MAPBOX_TOKEN` is not present. Default: `false`.
- `DEV_BYPASS_SCORING` — DEV only: bypass weather scoring and return nearest candidates directly from the dataset. Useful for UI demos when upstream weather is unavailable or slow. Default: `false`.
- `MAPBOX_TOKEN` — Mapbox geocoding token for production/staging geocode. Leave empty for local dev unless you want real Mapbox lookups.
- `DEV_ALLOW_CORS` — When `true`, enables permissive CORS for local frontend development.

Quick examples (PowerShell)

Start the backend with permissive CORS and dev geocode fallback:

    $env:DEV_ALLOW_CORS = 'true';
    $env:DEV_ALLOW_GEOCODE = 'true';
    & .venv\Scripts\uvicorn.exe Backend.main:app --reload --port 8000

Run the staging smoke checks against a running backend (default base http://127.0.0.1:8000):

    # run smoke script
    python Backend\scripts\staging_smoke.py --base http://127.0.0.1:8000

    # run smoke script with dev scoring bypass to return nearby dataset candidates
    $env:DEV_BYPASS_SCORING='true'; python Backend\scripts\staging_smoke.py --base http://127.0.0.1:8000

Add a demo dataset row (already done in this branch): we added `Volunteer Park` and two Seattle rows (`Gas Works Park`, `Discovery Park`) to `Backend/data/pnw.csv` for local demos.

Notes & safety

- Remove or set `DEV_BYPASS_SCORING=false` before pushing to staging/production. The dev bypass is intentionally destructive to production-like behavior (it skips weather and scoring).
- Keep `DEV_ALLOW_GEOCODE` off in staging/prod; instead, provision `MAPBOX_TOKEN` for staging to test real geocoding.
- If you see frequent 504s on `/recommend` for large radii, tune `WEATHER_FANOUT_MAX_CANDIDATES` or `REQUEST_BUDGET_MS` in your environment for staging.

If you want, I can also add a short GitHub Actions workflow to run the smoke script against a staging job as a post-deploy check. Ask me to add it and I will implement a minimal workflow file.
