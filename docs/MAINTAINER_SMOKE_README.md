Maintenance smoke steps for Unsplash meta->track dedupe verification

This short guide shows how a maintainer can run the integration smoke script
locally and in CI. It assumes the FastAPI backend is runnable from the
repository root (see `run_uvicorn.cmd` or the `Run FastAPI Server` task in
the workspace).

1) Local quick run (server already running)

```powershell
# from repo root
python Backend/scripts/integration_smoke.py --base-url http://127.0.0.1:8000 --photo-id smoke-maintainer --mock-trigger --dedupe-ttl 1
```

2) Local full run (start the server locally then run smoke)

```powershell
# Start the server in a separate terminal (reload ok for dev)
.\.venv\Scripts\uvicorn.exe main:app --reload --port 8000

# In another terminal, run the smoke
python Backend/scripts/integration_smoke.py --base-url http://127.0.0.1:8000 --photo-id smoke-maintainer --mock-trigger --dedupe-ttl 1
# To wait for readiness before running, add --wait
python Backend/scripts/integration_smoke.py --base-url http://127.0.0.1:8000 --photo-id smoke-maintainer --mock-trigger --wait --dedupe-ttl 1
```

3) CI usage notes

- The repository includes `.github/workflows/integration-smoke.yml` for a
  basic smoke run and `.github/workflows/integration-dedupe-matrix.yml` which
  runs a small matrix: varying `UNSPLASH_TRACK_DEDUPE_TTL` and a concurrency
  check that posts multiple simultaneous track calls to assert dedupe.
- CI requires these repository secrets to be configured for mock-trigger tests:
  - `SMOKE_BASE_URL` — the URL to the deployed/staging server (or set to http://127.0.0.1:8000 for self-hosted runners)
  - `UNSPLASH_TEST_HEADER_SECRET` — secret value used as `X-Test-Mock-Trigger` header

If you want me to also wire up GitHub Actions to run the matrix on PRs or
on a schedule, tell me which trigger you prefer and I'll add it.
