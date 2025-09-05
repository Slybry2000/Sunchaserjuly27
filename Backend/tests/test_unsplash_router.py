from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import time

from Backend.main import app
from Backend.utils.cache_inproc import cache as inproc_cache
from Backend.services.metrics import reset as metrics_reset, get_metrics

client = TestClient(app)


def teardown_function(_):
    # Clear the inproc cache between tests to avoid cross-test pollution
    inproc_cache.clear()
    metrics_reset()


def test_track_missing_fields():
    r = client.post('/internal/photos/track', json={})
    assert r.status_code == 400


@patch('Backend.routers.unsplash.ui.trigger_photo_download')
def test_track_success_and_dedupe(mock_trigger):
    mock_trigger.return_value = True

    payload = {'download_location': 'https://api.unsplash.com/photos/xyz/download'}
    r1 = client.post('/internal/photos/track', json=payload)
    assert r1.status_code == 200
    assert r1.json().get('tracked') is True

    # Second call should be deduped
    r2 = client.post('/internal/photos/track', json=payload)
    assert r2.status_code == 200
    assert r2.json().get('tracked') is False
    assert r2.json().get('reason') == 'deduped'
    # Metrics: one request, one success
    metrics = get_metrics()
    assert metrics.get('unsplash.track.requests_total', 0) == 1
    assert metrics.get('unsplash.track.success_total', 0) == 1


@patch('Backend.routers.unsplash.ui.trigger_photo_download')
def test_track_failure(mock_trigger):
    mock_trigger.return_value = False
    payload = {'photo_id': 'xyz'}
    r = client.post('/internal/photos/track', json=payload)
    assert r.status_code == 200
    assert r.json().get('tracked') is False
    metrics = get_metrics()
    assert metrics.get('unsplash.track.requests_total', 0) == 1
    assert metrics.get('unsplash.track.failure_total', 0) == 1


@patch('Backend.routers.unsplash.ui.trigger_photo_download')
def test_dedupe_ttl_expiry(mock_trigger):
    # Use a very small TTL so we can test expiry
    os.environ['UNSPLASH_TRACK_DEDUPE_TTL'] = '1'
    mock_trigger.return_value = True
    payload = {'photo_id': 'abc'}

    r1 = client.post('/internal/photos/track', json=payload)
    assert r1.status_code == 200
    assert r1.json().get('tracked') is True

    # Immediately deduped
    r2 = client.post('/internal/photos/track', json=payload)
    assert r2.json().get('tracked') is False

    # Wait for TTL to expire
    time.sleep(1.1)
    r3 = client.post('/internal/photos/track', json=payload)
    assert r3.status_code == 200
    assert r3.json().get('tracked') is True
    # Metrics: two requests, two successes (the middle deduped call doesn't increment requests_total)
    metrics = get_metrics()
    assert metrics.get('unsplash.track.requests_total', 0) == 2
    assert metrics.get('unsplash.track.success_total', 0) == 2


@patch('Backend.routers.unsplash.ui.trigger_photo_download')
def test_integration_meta_then_track(mock_trigger):
    """Integration-style test: simulate frontend flow:
    1. GET /internal/photos/meta to obtain download_location
    2. POST /internal/photos/track to register a view
    3. Repeat POST and assert dedupe
    """
    mock_trigger.return_value = True
    photo_id = 'integration-1'

    # Step 1: fetch meta
    rmeta = client.get(f'/internal/photos/meta?photo_id={photo_id}')
    assert rmeta.status_code == 200
    body = rmeta.json()
    download_location = body['links']['download_location']
    assert 'download' in download_location

    # Step 2: track
    r1 = client.post('/internal/photos/track', json={'download_location': download_location})
    assert r1.status_code == 200
    assert r1.json().get('tracked') is True

    # Step 3: repeated track -> deduped
    r2 = client.post('/internal/photos/track', json={'download_location': download_location})
    assert r2.status_code == 200
    assert r2.json().get('tracked') is False

    metrics = get_metrics()
    assert metrics.get('unsplash.track.requests_total', 0) >= 1
    assert metrics.get('unsplash.track.success_total', 0) >= 1
