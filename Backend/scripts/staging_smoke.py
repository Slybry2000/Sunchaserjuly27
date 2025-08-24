#!/usr/bin/env python3
"""Simple staging smoke test script.

Runs a few lightweight endpoint checks against the API and reports JSON output.
Exit code 0 means all core checks passed.

Usage: python Backend/scripts/staging_smoke.py [--base http://127.0.0.1:8000]
"""
from __future__ import annotations
import os
import json
import argparse
import httpx


def log(msg: str) -> None:
    print(msg)


def pretty(j: dict) -> str:
    return json.dumps(j, indent=2, default=str)


def run_check(base: str) -> int:
    client = httpx.Client(base_url=base, timeout=10.0)
    ok = True

    # Health
    try:
        r = client.get("/health")
        log(f"/health -> {r.status_code}")
        try:
            log(pretty(r.json()))
        except Exception:
            log(r.text)
        ok = ok and (r.status_code == 200)
    except Exception as e:
        log(f"/health request failed: {e}")
        return 2

    # Geocode (best-effort)
    try:
        r = client.get("/geocode", params={"q": "Seattle, WA"})
        log(f"/geocode?q=Seattle, WA -> {r.status_code}")
        try:
            log(pretty(r.json()))
        except Exception:
            log(r.text)
        # geocode may 400 if ENABLE_Q disabled; treat 200 as success, else warn
        if r.status_code != 200:
            log("/geocode did not return 200; check ENABLE_Q/MAPBOX_TOKEN or DEV_ALLOW_GEOCODE")
    except Exception as e:
        log(f"/geocode request failed: {e}")

    # Recommend with q
    try:
        r = client.get("/recommend", params={"q": "Seattle, WA", "radius": "25"})
        log(f"/recommend?q=Seattle,WA&radius=25 -> {r.status_code}")
        try:
            payload = r.json()
            log(pretty(payload))
        except Exception:
            log(r.text)

        if r.status_code == 200:
            etag = r.headers.get("ETag")
            if etag:
                log(f"ETag present: {etag}")
                # revalidate
                r2 = client.get("/recommend", params={"q": "Seattle, WA", "radius": "25"}, headers={"If-None-Match": etag})
                log(f"/recommend revalidate -> {r2.status_code}")
                if r2.status_code == 304:
                    log("Conditional request returned 304 Not Modified")
                else:
                    log("Conditional request did not return 304; got body or different ETag")
        else:
            ok = False
    except Exception as e:
        log(f"/recommend request failed: {e}")
        ok = False

    return 0 if ok else 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), help="Base URL for API")
    args = parser.parse_args(argv)

    log(f"Running staging smoke checks against {args.base}")
    rc = run_check(args.base)
    if rc == 0:
        log("SMOKE CHECKS PASSED")
    else:
        log(f"SMOKE CHECKS FAILED (code {rc})")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
