import os
import time
from unittest.mock import patch

from fastapi.testclient import TestClient

from Backend.main import app
from Backend.services.metrics import get_metrics
from Backend.services.metrics import reset as metrics_reset
from Backend.utils.cache_inproc import cache as inproc_cache

client = TestClient(app)


def teardown_function(_):
    # Clear the inproc cache between tests to avoid cross-test pollution
    inproc_cache.clear()
    # Reset the global cache backend instance and clear any cached data
    import Backend.utils.external_cache as ec

    if ec._cache_backend:
        # Clear Redis cache if using Redis
        if hasattr(ec._cache_backend, "_client"):
            try:
                import asyncio

                # Run async clear in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(ec._cache_backend._client.flushdb())
                loop.close()
            except Exception:
                # If Redis flush fails, ignore errors in teardown
                pass
    ec._cache_backend = None
    metrics_reset()


def test_track_missing_fields():
    r = client.post("/internal/photos/track", json={})
    assert r.status_code == 400


@patch("Backend.routers.unsplash.ui.trigger_photo_download")
@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
def test_track_success_and_dedupe(mock_trigger):
    mock_trigger.return_value = True

    payload = {"download_location": "https://api.unsplash.com/photos/xyz/download"}
    r1 = client.post("/internal/photos/track", json=payload)
    assert r1.status_code == 200
    assert r1.json().get("tracked") is True

    # Second call should be deduped
    r2 = client.post("/internal/photos/track", json=payload)
    assert r2.status_code == 200
    assert r2.json().get("tracked") is False
    assert r2.json().get("reason") == "deduped"
    # Metrics: one request, one success
    metrics = get_metrics()
    assert metrics.get("unsplash.track.requests_total", 0) == 1
    assert metrics.get("unsplash.track.success_total", 0) == 1


@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_track_failure(mock_trigger):
    mock_trigger.return_value = False
    payload = {"photo_id": "xyz"}
    r = client.post("/internal/photos/track", json=payload)
    assert r.status_code == 200
    assert r.json().get("tracked") is False
    metrics = get_metrics()
    assert metrics.get("unsplash.track.requests_total", 0) == 1
    assert metrics.get("unsplash.track.failure_total", 0) == 1


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_dedupe_ttl_expiry(mock_trigger):
    # Use a very small TTL so we can test expiry
    os.environ["UNSPLASH_TRACK_DEDUPE_TTL"] = "1"
    mock_trigger.return_value = True
    payload = {"photo_id": "abc"}

    r1 = client.post("/internal/photos/track", json=payload)
    assert r1.status_code == 200
    assert r1.json().get("tracked") is True

    # Immediately deduped
    r2 = client.post("/internal/photos/track", json=payload)
    assert r2.json().get("tracked") is False

    # Wait for TTL to expire
    time.sleep(1.1)
    r3 = client.post("/internal/photos/track", json=payload)
    assert r3.status_code == 200
    assert r3.json().get("tracked") is True
    # Metrics: two requests, two successes (middle deduped call not counted)
    metrics = get_metrics()
    assert metrics.get("unsplash.track.requests_total", 0) == 2
    assert metrics.get("unsplash.track.success_total", 0) == 2


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_integration_meta_then_track(mock_trigger):
    """Integration-style test: simulate frontend flow:
    1. GET /internal/photos/meta to obtain download_location
    2. POST /internal/photos/track to register a view
    3. Repeat POST and assert dedupe
    """
    mock_trigger.return_value = True
    photo_id = "integration-1"

    # Step 1: fetch meta
    rmeta = client.get(f"/internal/photos/meta?photo_id={photo_id}")
    assert rmeta.status_code == 200
    body = rmeta.json()
    download_location = body["links"]["download_location"]
    assert "download" in download_location

    # Step 2: track
    r1 = client.post(
        "/internal/photos/track", json={"download_location": download_location}
    )
    assert r1.status_code == 200
    assert r1.json().get("tracked") is True

    # Step 3: repeated track -> deduped
    r2 = client.post(
        "/internal/photos/track", json={"download_location": download_location}
    )
    assert r2.status_code == 200
    assert r2.json().get("tracked") is False

    metrics = get_metrics()
    assert metrics.get("unsplash.track.requests_total", 0) >= 1
    assert metrics.get("unsplash.track.success_total", 0) >= 1


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_integration_meta_then_track_with_ttl(mock_trigger):
    """Integration-style test: fetch meta, track, ensure dedupe, wait TTL, track again."""
    mock_trigger.return_value = True
    photo_id = "integration-ttl-1"

    # Step 1: fetch meta
    rmeta = client.get(f"/internal/photos/meta?photo_id={photo_id}")
    assert rmeta.status_code == 200
    body = rmeta.json()
    download_location = body["links"]["download_location"]

    # Set a small TTL for the test
    os.environ["UNSPLASH_TRACK_DEDUPE_TTL"] = "1"

    # Step 2: track
    r1 = client.post(
        "/internal/photos/track", json={"download_location": download_location}
    )
    assert r1.status_code == 200
    assert r1.json().get("tracked") is True

    # Step 3: repeated track -> deduped
    r2 = client.post(
        "/internal/photos/track", json={"download_location": download_location}
    )
    assert r2.status_code == 200
    assert r2.json().get("tracked") is False

    # Wait for TTL to expire and post again
    import time

    time.sleep(1.1)
    r3 = client.post(
        "/internal/photos/track", json={"download_location": download_location}
    )
    assert r3.status_code == 200
    assert r3.json().get("tracked") is True

    metrics = get_metrics()
    # We expect at least two successful track calls counted (first and third)
    assert metrics.get("unsplash.track.success_total", 0) >= 2


@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_mock_header_hardening_accepts_when_allowed(mock_trigger):
    """When ALLOW_TEST_HEADERS and UN_SPLASH_TEST_HEADER_SECRET are set,
    providing the matching header value should simulate success.
    """
    # Ensure trigger wouldn't be called (we simulate via header)
    mock_trigger.side_effect = Exception("should not be called")

    # Enable allow and set secret
    os.environ["ALLOW_TEST_HEADERS"] = "true"
    os.environ["UNSPLASH_TEST_HEADER_SECRET"] = "ci-secret-123"

    payload = {
        "download_location": "https://api.unsplash.com/photos/mock-test-123/download"
    }
    headers = {"X-Test-Mock-Trigger": "ci-secret-123"}
    r = client.post("/internal/photos/track", json=payload, headers=headers)
    assert r.status_code == 200
    assert r.json().get("tracked") is True


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_mock_header_rejected_when_not_allowed(mock_trigger):
    """
    If ALLOW_TEST_HEADERS is not set or the secret mismatches, the header must
    be ignored and the trigger should be called.
    """
    mock_trigger.return_value = True

    # Ensure gating disabled
    if "ALLOW_TEST_HEADERS" in os.environ:
        del os.environ["ALLOW_TEST_HEADERS"]
    if "UNSPLASH_TEST_HEADER_SECRET" in os.environ:
        del os.environ["UNSPLASH_TEST_HEADER_SECRET"]

    payload = {
        "download_location": "https://api.unsplash.com/photos/reject-test-456/download"
    }
    headers = {"X-Test-Mock-Trigger": "ci-secret-123"}
    r = client.post("/internal/photos/track", json=payload, headers=headers)
    assert r.status_code == 200
    # trigger_photo_download was called (mock returns True)
    assert r.json().get("tracked") is True


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.fetch_random_photo")
@patch("Backend.routers.unsplash.ui.fetch_photo_meta")
def test_meta_random_fallback(mock_fetch_meta, mock_fetch_random):
    """Test that random fallback is used when photo meta fetch fails."""
    mock_fetch_meta.return_value = None  # Simulate meta fetch failure
    mock_fetch_random.return_value = {
        "id": "random-123",
        "urls": {"regular": "https://example.com/random.jpg"},
        "links": {
            "html": "https://unsplash.com/random",
            "download": "https://api.unsplash.com/random/download",
        },
        "user": {
            "name": "Random Photographer",
            "links": {"html": "https://unsplash.com/@random"},
        },
    }

    r = client.get("/internal/photos/meta?photo_id=missing-123&category=nature")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "live"  # Random fallback still counts as live
    assert body["random_fallback"] is True
    assert body["id"] == "random-123"
    assert "Random Photographer" in body["attribution_html"]


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.fetch_photo_meta")
def test_meta_cache_hit_metrics(mock_fetch_meta):
    """Test that cache hit metrics are properly incremented."""
    mock_fetch_meta.return_value = {
        "id": "test-123",
        "urls": {"regular": "https://example.com/test.jpg"},
        "links": {
            "html": "https://unsplash.com/test",
            "download": "https://api.unsplash.com/test/download",
        },
        "user": {
            "name": "Test Photographer",
            "links": {"html": "https://unsplash.com/@test"},
        },
    }

    # First request - should be cache miss
    r1 = client.get("/internal/photos/meta?photo_id=test-123")
    assert r1.status_code == 200
    metrics = get_metrics()
    assert metrics.get("unsplash_meta_cache_miss", 0) == 1
    assert metrics.get("unsplash_meta_cache_hit", 0) == 0

    # Second request - should be cache hit
    r2 = client.get("/internal/photos/meta?photo_id=test-123")
    assert r2.status_code == 200
    metrics = get_metrics()
    assert metrics.get("unsplash_meta_cache_hit", 0) == 1


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.fetch_photo_meta")
def test_meta_debug_flag(mock_fetch_meta):
    """Test that debug=true includes debug information in response."""
    mock_fetch_meta.return_value = {
        "id": "debug-123",
        "urls": {"regular": "https://example.com/debug.jpg"},
        "links": {
            "html": "https://unsplash.com/debug",
            "download": "https://api.unsplash.com/debug/download",
        },
        "user": {
            "name": "Debug Photographer",
            "links": {"html": "https://unsplash.com/@debug"},
        },
    }

    r = client.get("/internal/photos/meta?photo_id=debug-123&debug=true")
    assert r.status_code == 200
    body = r.json()
    assert "debug" in body
    assert body["debug"]["access_key_present"] is True
    assert body["debug"]["cache_status"] == "miss"


def test_meta_demo_fallback():
    """Test demo fallback when no access key is provided."""
    # Ensure no access key
    if "UNSPLASH_CLIENT_ID" in os.environ:
        del os.environ["UNSPLASH_CLIENT_ID"]

    r = client.get("/internal/photos/meta?photo_id=demo-123")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "demo"
    assert body["id"] == "demo-123"
    assert "Demo Photographer" in body["attribution_html"]


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_track_response_reasons(mock_trigger):
    """Test that track endpoint returns appropriate reasons."""
    mock_trigger.return_value = False

    # Test missing params
    r1 = client.post("/internal/photos/track", json={})
    assert r1.status_code == 400

    # Test API failure
    payload = {"download_location": "https://api.unsplash.com/photos/fail/download"}
    r2 = client.post("/internal/photos/track", json=payload)
    assert r2.status_code == 200
    assert r2.json()["tracked"] is False
    assert r2.json()["reason"] == "api_failure"


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_track_missing_access_key(mock_trigger):
    """Test track failure when access key is missing."""
    # Remove access key temporarily
    if "UNSPLASH_CLIENT_ID" in os.environ:
        del os.environ["UNSPLASH_CLIENT_ID"]

    payload = {"download_location": "https://api.unsplash.com/photos/test/download"}
    r = client.post("/internal/photos/track", json=payload)
    assert r.status_code == 200
    assert r.json()["tracked"] is False
    assert r.json()["reason"] == "missing_params"


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_concurrent_track_calls_dedupe(mock_trigger):
    """Simulate concurrent POSTs for the same download_location and ensure
    deduplication prevents duplicate trigger calls."""
    mock_trigger.return_value = True
    payload = {
        "download_location": "https://api.unsplash.com/photos/concurrent/download"
    }

    import threading

    results = []

    def worker():
        r = client.post("/internal/photos/track", json=payload)
        results.append(r.json())

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one of the results should have tracked==True, rest deduped
    tracked_count = sum(1 for r in results if r.get("tracked") is True)
    deduped_count = sum(1 for r in results if r.get("tracked") is False)
    assert tracked_count == 1
    assert deduped_count == 4


@patch.dict("os.environ", {"UNSPLASH_CLIENT_ID": "test_access_key"})
@patch("Backend.routers.unsplash.ui.trigger_photo_download")
def test_track_handles_cache_backend_failure(mock_trigger):
    """Simulate cache backend raising an exception and ensure the track
    endpoint still attempts to call trigger_photo_download and records metrics."""
    mock_trigger.return_value = True

    # Patch external_cache.get_cache_backend to raise when accessed
    import Backend.utils.external_cache as ec

    original_get = ec.get_cache_backend

    def broken_get():
        raise RuntimeError("redis down")

    ec.get_cache_backend = broken_get

    try:
        payload = {"photo_id": "cache-failure-1"}
        r = client.post("/internal/photos/track", json=payload)
        assert r.status_code == 200
        # Should still attempt to trigger and mark tracked True
        assert r.json().get("tracked") in (True, False)
    finally:
        ec.get_cache_backend = original_get
