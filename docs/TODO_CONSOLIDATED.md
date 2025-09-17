# Consolidated TODOs and Production Launch Plan

This file centralizes outstanding work discovered across the repository (docs, backend, frontend, CI) and marks current status, evidence, and the prioritized order of tasks needed to reach a production launch for Unsplash-backed photo features.

---

## High-level status

- Current branch: `feature/unsplash-tracking`
- Backend: endpoints and helpers implemented and unit-tested (`/internal/photos/meta`, `/internal/photos/track`, `Backend/services/unsplash_integration.py`) — see `Backend/tests/*` for unit/integration tests.
- CI: integration smoke test and other checks are present in CI (CI reported 16/16 passing for the feature branch).
- Frontend: attribution rendering wired, but tappable links and screenshot artifacts are pending.

---

## Consolidated action list

Each item below includes: status (Done / Not Done), short description, evidence (file or doc), and priority (High/Medium/Low).

1. Photo hotlinking (use `photo.urls.regular` / `photo.urls.small`)
   - Status: Done
   - Evidence: `docs/UNSPLASH_PRODUCTION_CHECKLIST.md` (implementation examples), frontend wiring implemented (see `Frontend` files)
   - Priority: High

2. Download tracking endpoint & helper (`/internal/photos/track` + `triggerDownload`)
   - Status: Done
   - Evidence: `Backend/routers/unsplash.py`, `Backend/services/unsplash_integration.py`, `Backend/tests/test_unsplash_integration.py`
   - Priority: High

3. Server-side dedupe / short TTL cache for tracking
   - Status: Done
   - Evidence: `docs/UNSPLASH_PRODUCTION_CHECKLIST.md` (notes: server-side dedupe implemented), `Backend/tests/test_unsplash_router.py`
   - Priority: High

4. Server-side attribution helper `build_attribution_html(photo)`
   - Status: Done
   - Evidence: `Backend/services/unsplash_integration.py` and unit tests
   - Priority: High

5. Frontend attribution rendering (visible)
   - Status: Done
   - Evidence: `docs/UNSPLASH_APPLICATION_MATERIALS.md`, `docs/UNSPLASH_FRONTEND_EXAMPLE.md` (frontend wiring implemented)
   - Priority: High

6. Make attribution links tappable (frontend `url_launcher` or similar)
   - Status: Not Done
   - Evidence: `docs/UNSPLASH_PRODUCTION_CHECKLIST.md` (TODO: Make attribution links tappable)
   - Priority: High (required for Unsplash production compliance)

7. Visual distinction from Unsplash (branding, no Unsplash logo, color scheme)
   - Status: Partially Done / Needs review
   - Evidence: Docs emphasize it (`UNSPLASH_PRODUCTION_CHECKLIST.md`), but no formal design review artifacts or screenshots committed
   - Priority: Medium (required for submission review)

8. App description & representation accuracy (docs + README)
   - Status: Partially Done
   - Evidence: `docs/UNSPLASH_APPLICATION_MATERIALS.md` contains approved description; check README for parity
   - Priority: Medium

9. Capture required screenshots (attribution visible, tappable links, UI distinction)
   - Status: Not Done
   - Evidence: `docs/UNSPLASH_PRODUCTION_CHECKLIST.md` (Required Screenshots section)
   - Priority: High (required before submission)

10. CI integration of integration_smoke.py with secret mock header
    - Status: Partially Done / Verify
    - Evidence: Smoke script exists (`Backend/scripts/integration_smoke.py`) and docs reference CI usage; some notes indicate CI secrets configured, but confirm workflow uses the secret header.
    - Priority: High

11. Mock-header hardening & audit logging for mock usage (ALLOW_TEST_HEADERS gating)
    - Status: Done (implementation present) — please verify env in target CI/staging
    - Evidence: `docs/UNSPLASH_PRODUCTION_CHECKLIST.md` (notes saying `ALLOW_TEST_HEADERS` and `UNSPLASH_TEST_HEADER_SECRET` are implemented)
    - Priority: High

12. Ensure frontend does NOT contain Client-ID / secrets
    - Status: Not Done (manual verification required)
    - Evidence: Documentation recommends this; audit needed in frontend build artifacts
    - Priority: High (sensitive)

13. Frontend: use `visibility_detector` or equivalent to only track when image becomes visible
    - Status: Not Done (current wiring tracks on image-load; recommended enhancement)
    - Evidence: `docs/UNSPLASH_INTEGRATION.md` suggests using visibility-based tracking
    - Priority: Medium

14. Frontend widget-level dedupe to avoid repeated requests on mounts
    - Status: Not Done (optional enhancement)
    - Evidence: `docs/UNSPLASH_PRODUCTION_CHECKLIST.md` and CORS debugging notes
    - Priority: Low

15. CI: optional job to capture frontend screenshots and attach to PR
    - Status: Not Done
    - Evidence: Recommended in docs; artifacts not present
    - Priority: Medium

16. Observability: alerts for rate-limiting / failure spikes
    - Status: Partially Done (basic metrics implemented)
    - Evidence: `docs/UNSPLASH_PRODUCTION_CHECKLIST.md` (metrics listed); alerts need configuration in production monitoring
    - Priority: Medium

17. Final Unsplash application submission materials & submission
    - Status: Not Done (ready to be submitted once screenshots & tappable links are done)
    - Evidence: `docs/UNSPLASH_APPLICATION_MATERIALS.md` prepared; screenshots missing
    - Priority: High

---

## Action items marked Not Done (consolidated, ordered for production launch)

1. Make attribution links tappable in the frontend (use `url_launcher` or equivalent). (High)
   - Why first: required by Unsplash review and quick to implement.
   - Success criteria: attribution links open external browser to photographer profile and Unsplash photo page.

2. Capture required screenshots and attach to PR / docs. (High)
   - Why second: submission requires evidence; screenshots should show tappable links and UI distinction.
   - Success criteria: three screenshots (attribution example, main app screen, photo integration) stored in PR artifacts or `docs/screenshots/`.

3. Verify CI workflow uses the `UNSPLASH_TEST_HEADER_SECRET` for `--mock-trigger` smoke runs and that mock-header gating is enforced. (High)
   - Why third: ensures CI smoke tests are safe and repeatable; verifies new changes in server-side gating.
   - Success criteria: CI job invokes smoke script with header secret and job logs show simulated `tracked:true` path.

4. Audit frontend builds for accidental secret leakage (Client-ID in code or bundles). (High)
   - Why fourth: security — must not leak client secrets in frontend.
   - Success criteria: no Client-ID or secret in committed code or build artifacts.

5. Improve visibility-based tracking in frontend (use `visibility_detector`). (Medium)
   - Why: more accurate tracking and fewer duplicates than load-based triggers.

6. Add optional CI job to capture screenshots automatically (emulator or web). (Medium)
   - Why: automate proof artifacts for reviewers.

7. Design review / formal verification of visual distinction (colors, logo). (Medium)
   - Why: Unsplash review checks for UI distinctness.

8. Configure production alerts for tracking failures / rate limit spikes. (Medium)
   - Why: operational readiness.

---

## Quick verification commands

Run unit tests (backend):

```powershell
pytest Backend/tests -q
```

Run integration smoke locally (mocked):

```powershell
# Start server in one shell (single-process recommended):
# $env:UNSPLASH_CLIENT_ID='YOUR_KEY_HERE'; .\.venv\Scripts\python.exe -m uvicorn Backend.main:app --port 8000
# Then run smoke script (example):
python Backend/scripts/integration_smoke.py --mock-trigger --wait
```

Run full test suite:

```powershell
pytest -q
```

To enable end-to-end tests during local pytest runs set:

```powershell
$env:RUN_E2E='1'; pytest -q
```

---

## Proposed immediate work (I can implement)

- Implement frontend tappable attribution links and add a small widget/integration test that asserts links are present and that the frontend calls `/internal/photos/track` once on first visibility. (Estimated: 1 day)
- Capture required screenshots and commit them to `docs/screenshots/` or add to PR artifacts. (Estimated: 0.5 day)
- Verify CI smoke script uses secret header and update GitHub Actions if needed to include the `--mock-trigger` job (Estimated: 0.5 day)

If you'd like, I will start with implementing tappable attribution links in the frontend or the server-side verification of the CI smoke integration — tell me which and I'll proceed and report back with diffs and test runs.

---

Generated on: 2025-09-14
