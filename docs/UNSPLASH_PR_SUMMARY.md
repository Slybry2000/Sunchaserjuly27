PR Summary: Unsplash integration work

Files changed/added (high level):
- Backend/services/unsplash_integration.py  -- helper trigger + attribution
- Backend/routers/unsplash.py             -- /internal/photos/track, /internal/photos/meta
- Backend/tests/test_unsplash_integration.py
- Backend/tests/test_unsplash_router.py
- Backend/services/metrics.py (used existing)
- docs/UNSPLASH_IMPLEMENTATION.md
- docs/UNSPLASH_FRONTEND_EXAMPLE.md
- docs/UNSPLASH_API_README.md
- docs/UNSPLASH_PR_SUMMARY.md (this file)
- docs/UNSPLASH_PRODUCTION_CHECKLIST.md (updated)

Local test commands (PowerShell):
# Run the new backend tests
python -m pytest -q Backend/tests/test_unsplash_integration.py Backend/tests/test_unsplash_router.py

# Run the entire test suite
python -m pytest -q

Smoke run (manual):
# Start the app (example)
python -m uvicorn Backend.main:app --port 8000
# In another terminal, call the endpoints
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/internal/photos/meta?photo_id=abc"
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/internal/photos/track" -Body (ConvertTo-Json @{ download_location = 'https://api.unsplash.com/photos/abc/download' }) -ContentType 'application/json'

Reviewer checklist:
- [ ] All tests pass in CI
- [ ] No secrets committed
- [ ] Check `docs/UNSPLASH_FRONTEND_EXAMPLE.md` and verify it's practical for frontend devs
- [ ] Confirm metrics appear in staging after deploy
- [ ] Ensure screenshot attachments are uploaded to PR before merging

Notes:
- Dedupe is process-local. For multi-replica deployments, replace cache with Redis or central store.
- The Client-ID must be stored in secrets; backend reads `UNSPLASH_CLIENT_ID` env var.

*** End of PR summary
