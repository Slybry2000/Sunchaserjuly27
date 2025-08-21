Testing & HTTP mocking
=======================

Preferred mocking library
-------------------------

This project uses `pytest-httpx` (pinned in `requirements-dev.txt`) as the preferred HTTP mocking helper for tests. The `requirements-dev.txt` file contains a coordinated, validated set of dev pins (for example: `pytest-httpx==0.35.0`, `httpx==0.28.1`, `httpcore==1.0.9`, `h11==0.16.0`) that have been tested in CI.

Why `respx` is commented
------------------------

You may notice `respx==0.18.0` is commented in `requirements-dev.txt`. That version of `respx` requires a different `httpcore`/`httpx` family than the one pinned here and causes import/runtime incompatibilities when installed together. To keep CI deterministic and pip-audit clean, we keep `respx` commented by default.

If you want to experiment with `respx` locally
---------------------------------------------

1. Create an isolated environment (venv) so you can safely test alternate pins.
2. Try installing a `respx` release and compatible `httpx`/`httpcore` versions there.
3. Run the test subset you need and confirm CI implications (pip-audit, resolver).

Quick test commands
-------------------

Run the non-slow tests locally:

```powershell
pytest -k "not slow" -vv -x
```

Run the full test suite:

```powershell
pytest -vv
```

If you'd like, I can prototype a compatible `respx` + `httpx`/`httpcore` pinset in an isolated venv and report back with a recommended update and any pip-audit implications.
