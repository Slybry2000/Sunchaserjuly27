from fastapi import APIRouter, HTTPException, Body, Header
from pydantic import BaseModel
from typing import Optional
import logging
import os

from Backend.services import unsplash_integration as ui
from Backend.utils.cache_inproc import cache as inproc_cache
from Backend.services.metrics import incr as metrics_incr

router = APIRouter()
logger = logging.getLogger(__name__)


class TrackRequest(BaseModel):
    download_location: Optional[str] = None
    photo_id: Optional[str] = None


def _make_key(payload: TrackRequest) -> Optional[str]:
    if payload.download_location:
        return f"dl:{payload.download_location}"
    if payload.photo_id:
        return f"id:{payload.photo_id}"
    return None


@router.post('/internal/photos/track')
async def track_photo(payload: TrackRequest = Body(...), x_test_mock_trigger: Optional[str] = Header(None)):
    """Track a photo view. Centralizes the Unsplash download tracking call
    so the Client-ID remains server-side and de-duplicates repeated calls
    within a short TTL.
    """
    key = _make_key(payload)
    if not key:
        raise HTTPException(status_code=400, detail="missing download_location or photo_id")

    # TTL for dedupe can be configured with environment variable
    try:
        dedupe_ttl = int(os.environ.get('UNSPLASH_TRACK_DEDUPE_TTL', '300'))
    except Exception:
        dedupe_ttl = 300

    # Use process-local in-process cache to check for existing recent tracking
    existing, status = await inproc_cache.get_status(key)
    if status != 'miss':
        logger.debug('Deduped track request (cache status=%s) for %s', status, key)
        return {"tracked": False, "reason": "deduped"}

    # Insert a marker in cache optimistically to prevent immediate duplicates.
    # Set swr=0 so the marker is treated as expired (miss) after TTL instead
    # of falling into a stale-but-revalidatable state which would still be
    # treated as a dedupe.
    await inproc_cache.set(key, True, ttl=dedupe_ttl, swr=0)

    # Resolve download_location if only photo_id provided
    download_location = payload.download_location
    if not download_location and payload.photo_id:
        download_location = f"https://api.unsplash.com/photos/{payload.photo_id}/download"

    ACCESS_KEY = os.environ.get('UNSPLASH_CLIENT_ID')
    metrics_incr('unsplash.track.requests_total')

    # Support an internal test header which allows CI/tests to force a
    # successful trigger without making external network requests.
    # Hardening: only honor the mock header when the deployment explicitly
    # enables `ALLOW_TEST_HEADERS=true` and the provided header value matches
    # the server-side secret `UNSPLASH_TEST_HEADER_SECRET`.
    allow_test_headers = os.environ.get('ALLOW_TEST_HEADERS', '').lower() in ('1', 'true', 'yes')
    test_header_secret = os.environ.get('UNSPLASH_TEST_HEADER_SECRET')

    if allow_test_headers and test_header_secret and x_test_mock_trigger and x_test_mock_trigger == test_header_secret:
        # Log mock usage at info level for auditability; don't log secret value.
        logger.info('Mock Unsplash trigger honored for key=%s (test header used)', key)
        ok = True
    else:
        # If a test header was provided but not honored, log at debug for troubleshooting
        if x_test_mock_trigger:
            logger.debug('Mock header provided but not honored (allow=%s, secret_set=%s)', allow_test_headers, bool(test_header_secret))
        ok = ui.trigger_photo_download(download_location, ACCESS_KEY)
    if ok:
        metrics_incr('unsplash.track.success_total')
    else:
        metrics_incr('unsplash.track.failure_total')

    # Note: we keep the cache marker even if call fails to avoid tight retry loops.
    return {"tracked": bool(ok)}


@router.get('/internal/photos/meta')
async def photo_meta(photo_id: str):
    """Return a small photo metadata object the frontend can use.

    This endpoint is intentionally minimal and safe for tests. It returns
    `urls.regular`, `links.download_location`, and an attribution HTML
    snippet created by `build_attribution_html`.
    """
    # Build a simple synthetic photo object for demo/testing purposes
    photo = {
        "id": photo_id,
        "urls": {"regular": f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop"},
        "links": {"html": f"https://unsplash.com/photos/{photo_id}",
                  "download": f"https://api.unsplash.com/photos/{photo_id}/download"},
        "user": {"name": "Demo Photographer", "links": {"html": "https://unsplash.com/@demo"}},
    }

    # Use server-side helper to format attribution string
    attribution = ui.build_attribution_html(photo)

    return {
        "id": photo_id,
        "urls": photo["urls"],
        "links": {"download_location": photo["links"]["download"], "html": photo["links"]["html"]},
        "attribution_html": attribution,
    }
