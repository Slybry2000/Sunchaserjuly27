# Unsplash Backend API README

This doc describes the small set of backend endpoints and environment variables used for Unsplash integration in Sun Chaser.

Endpoints
- GET /internal/photos/meta?photo_id={id}
  - Returns a JSON object containing:
    - `id`
    - `urls.regular` - recommended hotlinked image URL
    - `links.download_location` - Unsplash download tracking URL
    - `links.html` - Unsplash photo page
    - `attribution_html` - server-rendered attribution snippet

- POST /internal/photos/track
  - Body: JSON with either `download_location` or `photo_id`
  - Calls Unsplash download endpoint server-side using `UNSPLASH_CLIENT_ID`.
  - Server-side dedupe prevents repeated tracking within a TTL (configurable).
  - Returns `{ "tracked": true|false, "reason": "deduped"? }`

Environment variables
- `UNSPLASH_CLIENT_ID` (required in production) - Unsplash Client ID used for download tracking
- `UNSPLASH_TRACK_DEDUPE_TTL` (optional, default 300) - dedupe window in seconds
 - `UNSPLASH_TEST_HEADER_SECRET` (CI only) - short-lived secret used by CI to request mock-trigger behavior. Store in your CI secrets and do NOT commit it.
 - `ALLOW_TEST_HEADERS` (CI only) - set to `true` in CI job env when you want to allow the mock header; should not be enabled in shared staging/production.

Metrics
- The tracking endpoint increments counters in `Backend.services.metrics`:
  - `unsplash.track.requests_total`
  - `unsplash.track.success_total`
  - `unsplash.track.failure_total`

Examples (PowerShell)

# Fetch photo meta
$meta = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/internal/photos/meta?photo_id=abc"
$meta.urls.regular

# Track photo view
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/internal/photos/track" -Body (ConvertTo-Json @{ download_location = $meta.links.download_location }) -ContentType 'application/json'

Tests
- Unit tests for helpers: `Backend/tests/test_unsplash_integration.py`
- Router and integration-style tests: `Backend/tests/test_unsplash_router.py`

CI setup for integration-smoke
- Add these secrets to your repository/organization secrets:
  - `UNSPLASH_TEST_HEADER_SECRET` — a short random token used by CI when invoking the smoke script.
  - `UNSPLASH_CLIENT_ID` — Unsplash Client ID for real download tracking (optional for smoke if using mock-trigger).
- Example GitHub Actions job environment (job-level `env`):

  env:
    ALLOW_TEST_HEADERS: 'true'
    UNSPLASH_TEST_HEADER_SECRET: ${{ secrets.UNSPLASH_TEST_HEADER_SECRET }}
    UNSPLASH_CLIENT_ID: ${{ secrets.UNSPLASH_CLIENT_ID }}

Notes: keep `UNSPLASH_TEST_HEADER_SECRET` short-lived or rotate periodically. Only enable `ALLOW_TEST_HEADERS` in ephemeral CI jobs; never enable it in production deployments.

Smoke script `--wait` flag
- The integration smoke script supports a `--wait` flag which causes the script to poll the API readiness endpoint (`/internal/photos/meta?photo_id=ci-smoke`) before running the meta->track flow.
- CI runs the smoke script with `--mock-trigger --wait` to avoid race conditions when the server is starting in the job.

Next steps
- Implement frontend wiring per `docs/UNSPLASH_FRONTEND_EXAMPLE.md` and capture screenshots for Unsplash application.
- Optionally replace in-process cache with Redis for cross-replica dedupe.
- Promote to production with `UNSPLASH_CLIENT_ID` injected from secrets manager and monitor metrics.

*** End of README
