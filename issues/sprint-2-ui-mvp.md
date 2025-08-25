---
name: Sprint 2 — UI MVP
labels: [sprint2, frontend]
---

Title: Sprint 2 — UI MVP

Body:

Tasks:
- Build minimal Flutter/FlutterFlow screens: Home (input) and Results (list)
- Wire UI to dummy data first; implement models for `RecommendResponse`
- Implement radius and date selectors; basic client-side filtering
- Add simple navigation and basic styling
 - Add unit tests for typed-search UI and `ApiClient.recommend(q: ...)` (mock HTTP) and verify ETag/304 behavior
 - Ensure Flutter CI (`.github/workflows/flutter-ci.yml`) is present and runs analyze + test on PRs
 - Update `Frontend/README.md` with quick run instructions including `--dart-define=API_BASE_URL` for dev and emulator hosts
 - Migrate existing `Radio` usages to the ancestor-driven `RadioGroup` API and remove deprecated `groupValue`/`onChanged` usage (resolve analyzer infos)
 - Implement `TelemetryService` contract used by `ApiClient` and wire telemetry calls to a local dev sink or noop implementation for offline dev

Acceptance criteria:
- App can show dummy results and navigate between screens
- Models match backend contract (v1) for quick integration
- Basic user flows are testable

Notes:
- Later sprints will integrate live data and ETag/304 client behavior.
