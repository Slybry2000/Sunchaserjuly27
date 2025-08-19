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

Acceptance criteria:
- Script can fetch and store forecasts for sample locations
- Scoring function returns reasonable values for known fixtures
- Tests covering parsing and scoring pass

Notes:
- Keep the implementation simple and testable; productionization steps later (scheduling, retries, monitoring).
