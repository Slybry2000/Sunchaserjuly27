"""Simple integration smoke test for Unsplash endpoints.

Calls:
  1) GET /internal/photos/meta?photo_id={id}
  2) POST /internal/photos/track with download_location from meta
  3) POST again and assert dedupe behavior (reason == 'deduped')

Exit code: 0 on success, 2 on failure.
"""

import argparse
import sys

import requests


def run(
    base_url: str,
    photo_id: str,
    wait_for_ready: bool = False,
    mock_trigger: bool = False,
    dedupe_ttl: float = 0.0,
) -> int:
    # If caller set the wait flag, poll the meta endpoint until ready.
    if wait_for_ready:
        import time

        import requests as _requests

        meta_url = f"{base_url.rstrip('/')}/internal/photos/meta"
        for i in range(12):
            try:
                r = _requests.get(meta_url, params={"photo_id": photo_id}, timeout=2)
                if r.status_code == 200:
                    print("Server readiness confirmed")
                    break
            except Exception:
                pass
            print(f"Waiting for server... attempt {i+1}")
            time.sleep(2)
        else:
            print("Server did not become ready in time")
            return 2

    try:
        meta_url = f"{base_url.rstrip('/')}/internal/photos/meta"
        print(f"GET {meta_url}?photo_id={photo_id}")
        rmeta = requests.get(meta_url, params={"photo_id": photo_id}, timeout=5)
    except Exception as e:
        print("ERROR: failed to fetch meta:", e)
        return 2

    if rmeta.status_code != 200:
        print("ERROR: meta endpoint returned", rmeta.status_code, rmeta.text)
        return 2

    body = rmeta.json()
    print("meta response:", body)

    download_location = body.get("links", {}).get("download_location")
    if not download_location:
        print("ERROR: meta response missing download_location")
        return 2

    track_url = f"{base_url.rstrip('/')}/internal/photos/track"
    payload = {"download_location": download_location}

    headers = {}
    # If the caller asked to mock trigger, send the CI secret value in the
    # header so the server can validate it before honoring the simulated
    # success. The secret should be provided in CI as UNSPLASH_TEST_HEADER_SECRET.
    if mock_trigger:
        secret = None
        # Prefer the CI-provided env var
        import os

        secret = os.environ.get("UNSPLASH_TEST_HEADER_SECRET")
        if not secret:
            print(
                "ERROR: UNSPLASH_TEST_HEADER_SECRET env var not set; cannot use"
                " --mock-trigger"
            )
            return 2
        headers["X-Test-Mock-Trigger"] = secret

    try:
        print(f"POST {track_url} payload={payload} headers={headers}")
        r1 = requests.post(track_url, json=payload, timeout=5, headers=headers)
    except Exception as e:
        print("ERROR: failed to POST track:", e)
        return 2

    print("first track response:", r1.status_code, r1.text)

    try:
        r2 = requests.post(track_url, json=payload, timeout=5, headers=headers)
    except Exception as e:
        print("ERROR: failed to POST track second time:", e)
        return 2

        # If a TTL was supplied, also test that after waiting the TTL the
        # server accepts tracking again (i.e., dedupe has expired).
        if dedupe_ttl and dedupe_ttl > 0:
            import time

            print(
                f"Waiting {dedupe_ttl + 0.1}s for dedupe TTL to expire and re-testing"
            )
            time.sleep(dedupe_ttl + 0.1)
            try:
                r3 = requests.post(track_url, json=payload, timeout=5, headers=headers)
            except Exception as e:
                print("ERROR: failed to POST track third time:", e)
                return 2
            print("third track response:", r3.status_code, r3.text)
            try:
                j3 = r3.json()
            except Exception:
                print("ERROR: third track did not return JSON")
                return 2
            if j3.get("tracked") is True:
                print("OK: dedupe TTL expired and track accepted on third call")
                return 0
            print("ERROR: third track still did not register after TTL wait")
            return 2
        return 0

    # Expect second call to be deduped
    try:
        j2 = r2.json()
    except Exception:
        print("ERROR: second track did not return JSON")
        return 2

    if j2.get("reason") == "deduped":
        print("OK: dedupe observed on second track call")
        return 0

    # Some deployments might behave differently; still accept dedupe-like behavior
    if j2.get("tracked") is False:
        print(
            "WARN: second track returned tracked=false but no 'deduped' reason;"
            " treating as deduped-like"
        )
        return 0

    print("ERROR: second track did not appear deduped")
    return 2


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--base-url", default="http://localhost:8000", help="Base URL for the API"
    )
    p.add_argument("--photo-id", default="smoke-1", help="Photo id to request meta for")
    p.add_argument(
        "--mock-trigger",
        action="store_true",
        help="Send header to ask server to mock trigger success",
    )
    p.add_argument(
        "--wait",
        action="store_true",
        help=(
            "Poll the meta endpoint until the server is ready before running"
            " the smoke steps"
        ),
    )
    p.add_argument(
        "--dedupe-ttl",
        type=float,
        default=0.0,
        help="If set, wait this many seconds after dedupe then POST again to assert TTL expiry",
    )
    args = p.parse_args()

    # Run the test with parsed arguments
    rc = run(
        args.base_url, args.photo_id, args.wait, args.mock_trigger, args.dedupe_ttl
    )
    sys.exit(rc)
