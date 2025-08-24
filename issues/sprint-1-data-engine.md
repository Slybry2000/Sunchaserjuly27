---
name: Sprint 1 — Forecast Data Engine
labels: [sprint1, backend]
---

Title: Sprint 1 — Forecast Data Engine

Body:

Tasks:
- Implement a backend job to fetch forecasts for ~100 test locations
- Normalize provider responses to a common hourly slot format
- Compute Sun Confidence Score (simple heuristic: cloud% threshold + duration, or agreement across providers)
- Persist processed results to Firestore or local store
- Add unit tests for parsing and scoring
 - Add dev dataset demo rows (Seattle area) so local `?q=` demos return results
 - Add `Backend/scripts/staging_smoke.py` to run health, geocode, recommend, and ETag checks; make it runnable from PowerShell for staging smoke tests
 - Add `docs/DEVELOPMENT.md` documenting `ENABLE_Q`, `DEV_ALLOW_GEOCODE`, `DEV_BYPASS_SCORING`, and example run commands
 - Add a small unit test for `?q=` flow exercising `DEV_BYPASS_SCORING` to ensure deterministic demo output

Acceptance criteria:
- Script can fetch and store forecasts for sample locations
- Scoring function returns reasonable values for known fixtures
- Tests covering parsing and scoring pass

Notes:
- Keep the implementation simple and testable; productionization steps later (scheduling, retries, monitoring).
