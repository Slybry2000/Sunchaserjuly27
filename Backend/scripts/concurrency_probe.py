#!/usr/bin/env python3
"""Simple concurrency probe used by CI to assert dedupe under concurrent posts."""
import os
import sys
import requests
import concurrent.futures


def main():
    base = os.environ.get("BASE_URL") or os.environ.get("SMOKE_BASE_URL") or "http://127.0.0.1:8000"
    secret = os.environ.get("UNSPLASH_TEST_HEADER_SECRET", "")
    try:
        meta = requests.get(base.rstrip("/") + "/internal/photos/meta", params={"photo_id": "ci-concurrency"}, timeout=5)
        meta.raise_for_status()
        meta_json = meta.json()
    except Exception as e:
        print("ERROR: failed to fetch meta:", e)
        return 2

    dl = (meta_json.get("links") or {}).get("download_location")
    if not dl:
        print("ERROR: meta missing download_location")
        return 2

    payload = {"download_location": dl}
    headers = {"X-Test-Mock-Trigger": secret} if secret else {}

    def post():
        try:
            r = requests.post(base.rstrip("/") + "/internal/photos/track", json=payload, headers=headers, timeout=5)
            try:
                return r.json()
            except Exception:
                return {"status": r.status_code, "text": r.text}
        except Exception as e:
            return {"error": str(e)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: post(), range(5)))

    print("results", results)
    tracked_count = sum(1 for r in results if r.get("tracked") is True)
    deduped_count = sum(1 for r in results if r.get("tracked") is False)
    print("tracked_count", tracked_count, "deduped_count", deduped_count)
    if tracked_count != 1:
        print("ERROR: expected exactly one tracked==True")
        return 2
    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
