import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Header, HTTPException

from Backend.models.unsplash import PhotoMetaResponse, TrackRequest, TrackResponse
from Backend.services import unsplash_integration as ui
from Backend.services.metrics import incr as metrics_incr
from Backend.utils.debug_logging import debug_log
from Backend.utils.external_cache import get_cache_backend
from Backend.utils.rate_limiter import check_rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)


def _make_key(payload: TrackRequest) -> Optional[str]:
    if payload.download_location:
        return f"dl:{payload.download_location}"
    if payload.photo_id:
        return f"id:{payload.photo_id}"
    return None


@router.post("/internal/photos/track")
async def track_photo(
    payload: TrackRequest = Body(...),
    x_test_mock_trigger: Optional[str] = Header(default=None),
):
    """Track a photo view. Centralizes the Unsplash download tracking call
    so the Client-ID remains server-side and de-duplicates repeated calls
    within a short TTL.
    """
    key = _make_key(payload)
    if not key:
        raise HTTPException(
            status_code=400, detail="missing download_location or photo_id"
        )

    # Apply rate limiting
    if not check_rate_limit(f"track:{key}"):
        logger.warning(f"Rate limit exceeded for track request: {key}")
        return TrackResponse(tracked=False, reason="rate_limited")

    # TTL for dedupe can be configured with environment variable
    try:
        dedupe_ttl = int(os.environ.get("UNSPLASH_TRACK_DEDUPE_TTL", "300"))
    except Exception:
        dedupe_ttl = 300

    # Use external cache backend (supports Redis when configured)
    cache_backend = get_cache_backend()
    existing, status = await cache_backend.get_status(key)
    if status != "miss":
        logger.debug("Deduped track request (cache status=%s) for %s", status, key)
        return TrackResponse(tracked=False, reason="deduped")

    # Insert a marker in cache optimistically to prevent immediate duplicates.
    # Set swr=0 so the marker is treated as expired (miss) after TTL instead
    # of falling into a stale-but-revalidatable state which would still be
    # treated as a dedupe.
    await cache_backend.set(key, True, ttl=dedupe_ttl, swr=0)

    # Resolve download_location if only photo_id provided
    download_location = payload.download_location
    if not download_location and payload.photo_id:
        download_location = (
            "https://api.unsplash.com/photos/" + payload.photo_id + "/download"
        )

    ACCESS_KEY = os.environ.get("UNSPLASH_CLIENT_ID")
    metrics_incr("unsplash.track.requests_total")

    # Support an internal test header which allows CI/tests to force a
    # successful trigger without making external network requests.
    # Hardening: only honor the mock header when the deployment explicitly
    # enables `ALLOW_TEST_HEADERS=true` and the provided header value matches
    # the server-side secret `UNSPLASH_TEST_HEADER_SECRET`.
    # Additional security: never allow in production environments
    is_production = os.environ.get("APP_ENV", "").lower() in ("prod", "production")
    allow_test_headers = (
        os.environ.get("ALLOW_TEST_HEADERS", "").lower() in ("1", "true", "yes")
        and not is_production
    )
    test_header_secret = os.environ.get("UNSPLASH_TEST_HEADER_SECRET")

    reason: Optional[str] = None
    if (
        allow_test_headers
        and test_header_secret
        and x_test_mock_trigger
        and x_test_mock_trigger == test_header_secret
    ):
        # Log mock usage at info level for auditability; don't log secret value.
        logger.info("Mock Unsplash trigger honored for key=%s (test header used)", key)
        ok = True
        reason = "mocked"
    else:
        # If a test header was provided but not honored, log at debug for help
        if x_test_mock_trigger:
            logger.debug(
                "Mock header present but not honored (allow=%s, secret_set=%s)",
                allow_test_headers,
                bool(test_header_secret),
            )

        # Ensure we have required parameters for the real API call
        if download_location and ACCESS_KEY:
            ok = ui.trigger_photo_download(download_location, ACCESS_KEY)
            reason = "api_failure" if not ok else None
        else:
            logger.error(
                "Missing required parameters: download_location=%s, ACCESS_KEY=%s",
                bool(download_location),
                bool(ACCESS_KEY),
            )
            ok = False
            reason = "missing_params"

    if ok:
        metrics_incr("unsplash.track.success_total")
    else:
        metrics_incr("unsplash.track.failure_total")

    # Note: we keep the cache marker even if call fails to avoid tight retry loops.
    return TrackResponse(tracked=bool(ok), reason=reason)


@router.get("/internal/photos/meta")
async def photo_meta(
    photo_id: str,
    category: Optional[str] = None,
    debug: bool = False,
    x_debug_unsplash_key: Optional[str] = Header(default=None),
):
    """Return minimal photo metadata + attribution.

    Attempts live Unsplash fetch when credentials provided; otherwise falls
    back to a deterministic synthetic object (demo). This keeps frontend logic
    stable regardless of environment.
    """
    access_key = os.environ.get("UNSPLASH_CLIENT_ID")
    # 'live' was previously assigned but not used; remove to satisfy linters.
    # Support dev-only header 'X-Debug-Unsplash-Key' to override UNSPLASH_CLIENT_ID.
    # Strictly for local debugging; do not rely on it in production.
    if not access_key and x_debug_unsplash_key:
        access_key_to_use = x_debug_unsplash_key
        access_key_source = "header"
    else:
        access_key_to_use = access_key or ""
        access_key_source = "env" if access_key else "none"

    # Cache key per photo id; category only influences live random fallback on failure.
    cache_key = f"unsplash:meta:{photo_id}"
    cache_backend = get_cache_backend()
    cache_value, cache_status = await cache_backend.get_status(cache_key)

    # Extract ETag from cached value if available
    cached_etag = None
    if cache_value and isinstance(cache_value, dict):
        cached_etag = cache_value.get("etag")

    def compute_result() -> Dict[str, Any]:
        """Sync factory: compute minimal meta, using live fetch when possible."""
        photo: Dict[str, Any] = {}
        live_local = None
        used_random = False
        if access_key_to_use:
            try:
                debug_log(
                    (
                        "router_pre_fetch: photo_id=%s access_key_present=%s "
                        "source=%s pid=%s"
                    )
                    % (
                        photo_id,
                        bool(access_key_to_use),
                        access_key_source,
                        os.getpid(),
                    )
                )
            except Exception:
                pass
            live_local = ui.fetch_photo_meta(
                photo_id, access_key_to_use, etag=cached_etag
            )  # Keep sync for now, can be async later
            try:
                debug_log(
                    "router_helper_report: live_present=%s pid=%s"
                    % (bool(live_local), os.getpid())
                )
            except Exception:
                pass
            if live_local and "data" in live_local:
                photo = live_local["data"]
                try:
                    debug_log(
                        "router_assigned_live: photo_user=%s keys=%s pid=%s"
                        % (
                            (photo.get("user") or {}).get("name"),
                            list(photo.keys()),
                            os.getpid(),
                        )
                    )
                except Exception:
                    pass
            elif category:
                rand = ui.fetch_random_photo(category, access_key_to_use)
                if rand:
                    used_random = True
                    live_local = {"data": rand}
                    photo = rand
                    try:
                        debug_log(
                            "router_assigned_random: cat=%s id=%s pid=%s"
                            % (category, photo.get("id"), os.getpid())
                        )
                    except Exception:
                        pass

        if not photo:
            # fallback synthetic demo object
            regular_url = (
                "https://images.unsplash.com/" + photo_id + "?auto=format&fit=crop"
            )
            html_url = "https://unsplash.com/photos/" + photo_id
            download_url = (
                "https://api.unsplash.com/photos/" + photo_id + "/download"
            )
            photo = {
                "id": photo_id,
                "urls": {"regular": regular_url},
                "links": {"html": html_url, "download": download_url},
                "user": {
                    "name": "Demo Photographer",
                    "links": {"html": "https://unsplash.com/@demo"},
                },
            }

        attribution = ui.build_attribution_html(photo)
        download_location = (photo.get("links") or {}).get("download")
        html_link = (photo.get("links") or {}).get("html")
        result_local = {
            "id": photo.get("id") or photo_id,
            "urls": photo.get("urls") or {},
            "links": {"download_location": download_location, "html": html_link},
            "attribution_html": attribution,
            "source": "live" if live_local else "demo",
        }
        if used_random:
            result_local["random_fallback"] = True
        # Include ETag in result for caching
        if live_local and "etag" in live_local:
            result_local["etag"] = live_local["etag"]
        return result_local

    # Use in-proc cache to reduce Unsplash API calls
    ttl_seconds = int(os.getenv("UNSPLASH_META_TTL", "3600"))
    swr_seconds = int(os.getenv("UNSPLASH_META_SWR", "600"))
    if cache_status != "miss":
        metrics_incr("unsplash_meta_cache_hit")
    else:
        metrics_incr("unsplash_meta_cache_miss")
    result = await cache_backend.get_or_set(
        cache_key, compute_result, ttl=ttl_seconds, swr=swr_seconds
    )
    # Debug: log minimal info about the response and access key source
    try:
        # Log compact debug info (keep message short to satisfy linters)
        debug_log(
            "router_debug: keys=%s source=%s pid=%s"
            % (list(result.keys()), result.get("source"), os.getpid(),)
        )
    except Exception:
        pass
    # Metrics for live/demo and random fallback
    metrics_incr(
        "unsplash_meta_live" if result.get("source") == "live" else "unsplash_meta_demo"
    )
    if result.get("random_fallback"):
        metrics_incr("unsplash_meta_random_fallback")

    # Dev-only debug output: when debug=true, include cache status and key source
    debug_info = None
    if debug:
        debug_info = {
            "access_key_present": bool(access_key),
            "access_key_source": access_key_source,
            "x_debug_unsplash_key_present": bool(x_debug_unsplash_key),
            "cache_status": cache_status,
        }

    return PhotoMetaResponse(
        id=result["id"],
        urls=result["urls"],
        links=result["links"],
        attribution_html=result["attribution_html"],
        source=result["source"],
        random_fallback=result.get("random_fallback"),
        debug=debug_info,
    )
