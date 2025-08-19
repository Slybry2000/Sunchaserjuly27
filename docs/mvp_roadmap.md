# Sun Chaser — One‑page MVP Roadmap

Objective

Launch a scrappy MVP for “clear skies” discovery quickly with minimal cost and fast execution.

Sprint 0 — Setup & Foundation (1–2 days)

- Create project environment (Firebase or minimal VPS) and repo scaffolding
- Register 2–3 weather forecast APIs (Open‑Meteo / OpenWeatherMap / Weatherbit) and record keys in `.env`
- Acquire and upload a small U.S. locations dataset (GeoNames/SimpleMaps) or use `data/pnw.csv` for initial testing
- Verify local dev run: `uvicorn main:app --reload`

Success: Firebase/APIs ready or local backend runs; dataset accessible

Sprint 1 — Forecast Data Engine (3–4 days)

- Implement a backend task (Python script or Cloud Function) to fetch forecasts for ~100 locations
- Normalize cloud cover and temperature into a simple slot shape
- Compute a simple Sun Confidence Score (agreement or weighted average across providers / or single provider with heuristics)
- Persist processed forecast & score to a datastore (Firestore or local JSON/SQLite)
- Add a small set of tests for parsing and scoring

Success: Forecast data stored; manual verification of Sun Confidence values

Sprint 2 — UI MVP (3–5 days)

- Minimal Flutter (or FlutterFlow) UI with:
  - Location input (lat/lon or query)
  - Radius selector and date picker
  - "Find Clear Skies" action that displays a ranked list
- Results screen: list of locations with Sun Confidence, cloud%, brief forecast
- Use dummy data first, then switch to live data

Success: Basic user flow works with test data

Sprint 3 — Integration & Polish (2–4 days)

- Connect frontend to backend or Firestore
- Implement error handling and empty-state UX
- Add ETag/304 handling on backend and basic client caching for repeated queries

Success: End‑to‑end search with live data and caching behavior

Minimal DoD

- `/recommend` (or client query) returns top‑N results with deterministic JSON and an `ETag`
- Basic CI: lint + tests pass; core tests exercise parsing, scoring, and the router
- Basic observability: request id + structured logs

Notes

- Full engineering plan and test matrix live in `docs/plan_vertical_slice.md` (detailed cache semantics, SWR, single‑flight, pytest config, etc.)
- I added issue drafts (folder `issues/`) you can convert into real GitHub issues via the `gh` CLI or create them manually in the repo Issues tab.

---

(If you want, I can open the first 3 GitHub issues directly — I'll need the local `gh` CLI authenticated; otherwise run the included script `scripts/create_github_issues.sh`.)
