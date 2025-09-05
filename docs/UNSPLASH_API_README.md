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

Next steps
- Implement frontend wiring per `docs/UNSPLASH_FRONTEND_EXAMPLE.md` and capture screenshots for Unsplash application.
- Optionally replace in-process cache with Redis for cross-replica dedupe.
- Promote to production with `UNSPLASH_CLIENT_ID` injected from secrets manager and monitor metrics.

*** End of README
