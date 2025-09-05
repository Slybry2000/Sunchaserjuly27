<!--
PR template for Unsplash integration-smoke changes.
This file is intended to be used as the PR body when opening a pull request that wires the integration smoke job into CI.
-->

## Unsplash integration smoke: CI wiring and secrets

Summary
-------
We added an integration smoke test to validate the Unsplash meta -> track -> dedupe flow in CI without calling Unsplash directly. This PR wires the smoke script into CI and hardens the server-side test hook.

Required repository secrets (add under Settings → Secrets and variables → Actions)
- `UNSPLASH_CLIENT_ID` — your Unsplash Access Key (Client ID). Server-only; do NOT put this in frontend code.
- `UNSPLASH_TEST_HEADER_SECRET` — a short random token (CI-only) used to gate mock success behavior. Generate a strong random value and store it here.

How CI uses the secrets
-----------------------
- The workflow job sets:
  - `ALLOW_TEST_HEADERS: 'true'` (job env)
  - `UNSPLASH_TEST_HEADER_SECRET: ${{ secrets.UNSPLASH_TEST_HEADER_SECRET }}`
  - `UNSPLASH_CLIENT_ID: ${{ secrets.UNSPLASH_CLIENT_ID }}`
- The job starts the FastAPI server, polls readiness, then runs:

```
python Backend/scripts/integration_smoke.py --base-url http://127.0.0.1:8000 --photo-id ci-smoke --mock-trigger --wait
```

- The smoke script sends the `X-Test-Mock-Trigger` header with the value from `UNSPLASH_TEST_HEADER_SECRET`. The server only honors the mock if `ALLOW_TEST_HEADERS=true` and the header value exactly matches the secret.

Reviewer verification steps
---------------------------
1. Confirm the two secrets are present in repo Secrets.
2. Open Actions → the workflow run for this PR (integration-smoke).
3. Verify the job succeeds and the smoke script logs show the mock path:
   - look for a log like: `Mock Unsplash trigger honored` or smoke output showing `tracked: true` on the first POST and a dedupe result on the second.
4. Confirm no secrets are printed in logs (Actions should redact secrets automatically).
5. Optionally, verify metrics were incremented and/or review the router audit log entry for the mock usage timestamp.

Quick local test (PowerShell)
-----------------------------
```powershell
$env:UNSPLASH_TEST_HEADER_SECRET = '<paste-secret-here>'
$env:UNSPLASH_CLIENT_ID = '<paste-client-id-here>'
python Backend/scripts/integration_smoke.py --base-url http://127.0.0.1:8000 --photo-id smoke-local --mock-trigger --wait
```

Notes and security
------------------
- `UNSPLASH_TEST_HEADER_SECRET` is not an Unsplash credential — generate it locally (base64 or random token) and rotate periodically.
- Never enable `ALLOW_TEST_HEADERS` in shared staging or production; use only in ephemeral CI job envs.

If you need help adding the secrets or validating the Actions run, paste the run URL or the Actions log and I can review the output.
