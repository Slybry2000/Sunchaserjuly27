Release note: Stabilize ETag behavior, tests, and CI

Summary

This change tightens ETag generation and makes several test and CI improvements to make Phase B backend tests deterministic and CI-friendly.

What changed

- Implemented canonical JSON serialization + SHA-256 strong ETag generation (deterministic across runs).
- Updated routers to compute and honor ETag / If-None-Match semantics (returns 304 where appropriate).
- Added focused ETag tests (invariance and round-trip) and deterministic cache-refresh fixture so background cache refreshes don't introduce flakiness in tests.
- Made pytest-asyncio work reliably in CI by enabling auto asyncio mode via `pytest.ini` and ensuring `pytest-asyncio` is installed in dev deps.
- Coordinated dev/test dependency pins to avoid pip resolver conflicts while remediating advisories: pytest==8.4.1, pytest-asyncio==1.1.0, pytest-httpx==0.35.0, httpx==0.28.1, httpcore==1.0.9, h11==0.16.0.
- CI workflow updated to install runtime + dev/test requirements before running pytest and pip-audit.

Files of note

- `Backend/utils/etag.py` — canonicalization + strong ETag helper
- `Backend/routers/*` — ETag integration
- `Backend/tests/*` — ETag invariance/roundtrip tests and deterministic cache fixture
- `requirements-dev.txt` — coordinated dev/test pins (httpx/httpcore/h11 + pytest upgrades)
- `pytest.ini` — `asyncio_mode = auto` to enable plain `async def` tests
- `Backend/tests/conftest.py` — autouse fixture `CACHE_REFRESH_SYNC` (deterministic cache refresh) and plugin discovery fixes
- CI workflow(s) — install dev/test deps before pytest and run pip-audit

CI status & notes

- The latest Python Tests CI run for this branch completed successfully: 58 tests passed and `pip-audit` reported "No known vulnerabilities found" for the pinned set.
- Codecov upload failed due to a missing token (non-blocking for tests).

Reviewer notes

- The dependency pins were coordinated to avoid resolver conflicts; consider periodic review and updating of the pinned set.
- If you prefer a different HTTP mocking library, `respx` is listed as an optional/dev-only choice in `requirements-dev.txt` (commented).

Next steps

- Consider adding a short CI job to run `pip-audit` on a daily schedule to catch new advisories early.
- If you want, I can also open a PR description on GitHub using this text (I will create the PR now).
