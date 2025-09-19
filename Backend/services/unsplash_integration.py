"""Small helpers for Unsplash integration.

- trigger_photo_download(download_location, access_key):
    calls Unsplash download endpoint
- build_attribution_html(photo): returns a small HTML snippet for
    attribution links
- fetch_photo_meta(photo_id, access_key): fetch photo metadata
- fetch_random_photo(query, access_key): fetch random photo by query

These are intentionally small and dependency-light so they can be used from
both API handlers and background tasks.
"""

import logging
from typing import Dict, Optional

import requests

from Backend.utils.circuit_breaker import get_unsplash_circuit_breaker
from Backend.utils.debug_logging import debug_log
from Backend.utils.http_client import async_get

logger = logging.getLogger(__name__)


def trigger_photo_download(
    download_location: str, access_key: str, timeout: float = 5.0
) -> bool:
    """Trigger Unsplash "download" endpoint for tracking photo usage.

    Args:
    download_location: the photo.links.download_location value returned by Unsplash.
        access_key: Unsplash Client ID (not a secret in the same sense as private keys).
        timeout: request timeout in seconds.

    Returns:
        True if the request succeeded (2xx/3xx), False otherwise.

    Notes:
        This function performs a GET request to the provided download_location and
        attaches the required Authorization header per Unsplash guidelines.
    """
    if not download_location or not access_key:
        logger.debug(
            "trigger_photo_download called with empty download_location or access_key"
        )
        return False

    # Check circuit breaker
    circuit_breaker = get_unsplash_circuit_breaker()
    if circuit_breaker.is_open:
        logger.warning("Unsplash circuit breaker is open, skipping download tracking")
        return False

    # Per Unsplash API guidelines, include Accept-Version header along with Client-ID
    headers = {
        "Authorization": f"Client-ID {access_key}",
        "Accept-Version": "v1",
    }
    try:
        debug_log(
            "trigger_photo_download: url=%s timeout=%s" % (download_location, timeout)
        )
        resp = requests.get(download_location, headers=headers, timeout=timeout)

        # Log status and a short snippet of the body for troubleshooting.
        # Some tests may patch `requests.get` with a Mock that does not
        # behave exactly like a `requests.Response` (e.g., Mock objects are
        # not subscriptable). Coerce to str() to avoid TypeError when
        # slicing or subscripting in logs.
        raw_text = getattr(resp, "text", "")
        try:
            body_snippet = (str(raw_text) or "")[:1000]
        except Exception:
            body_snippet = ""
        logger.debug(
            "Unsplash download tracking response: %s %s", resp.status_code, body_snippet
        )
        debug_log(
            "trigger_photo_download: status=%s body=%s"
            % (resp.status_code, body_snippet)
        )

        # Handle different status codes appropriately
        if resp.status_code == 429:
            # Rate limited - this counts as a failure for circuit breaker
            circuit_breaker._record_failure()
            logger.warning("Unsplash download tracking rate limited")
            return False
        elif 200 <= resp.status_code < 300:
            # Success - reset circuit breaker on success
            if (
                hasattr(circuit_breaker, "_state")
                and circuit_breaker._state.name == "HALF_OPEN"
            ):
                circuit_breaker._record_success()
            return True
        elif 300 <= resp.status_code < 400:
            # Redirects are also considered successful for tracking
            if (
                hasattr(circuit_breaker, "_state")
                and circuit_breaker._state.name == "HALF_OPEN"
            ):
                circuit_breaker._record_success()
            return True
        else:
            # Other errors - record as failure
            circuit_breaker._record_failure()
            logger.warning(
                "Unsplash download tracking failed with status: %s", resp.status_code
            )
            return False

    except Exception as exc:
        # Log exception with stack trace at debug to aid diagnosis without failing
        logger.exception("Failed to call Unsplash download endpoint")
        debug_log("trigger_photo_download: exception=%s" % (exc,))
        # Record failure for circuit breaker
        circuit_breaker._record_failure()
        return False


def build_attribution_html(photo: Dict) -> str:
    """Return a short HTML attribution snippet for embedding in UI.

    Expects `photo` to be an object/dict matching Unsplash photo response shape
    (at least `user.name`, `user.links.html`, and `links.html`).
    """
    if not photo:
        return ""

    user = photo.get("user") or {}
    user_name = user.get("name") or "Unknown"
    user_link = (user.get("links") or {}).get("html") or "#"
    photo_link = (photo.get("links") or {}).get("html") or "#"

    # Simple, accessible HTML attribution. Frontends are free to render this
    # as native widgets instead of raw HTML.
    return (
        'Photo by <a href="'
        + user_link
        + '" rel="nofollow noopener noreferrer" '
        + 'target="_blank">'
        + user_name
        + '</a> on <a href="'
        + photo_link
        + '" rel="nofollow noopener noreferrer" target="_blank">Unsplash</a>'
    )


def _trim_photo_data(data: Dict) -> Dict:
    """Trim Unsplash photo response to minimal needed fields."""
    return {
        "id": data.get("id"),
        "urls": {"regular": (data.get("urls") or {}).get("regular")},
        "links": {
            "html": (data.get("links") or {}).get("html"),
            "download": (data.get("links") or {}).get("download_location")
            or (data.get("links") or {}).get("download"),
        },
        "user": {
            "name": (data.get("user") or {}).get("name"),
            "links": {
                "html": ((data.get("user") or {}).get("links") or {}).get("html")
            },
        },
    }


def fetch_photo_meta(
    photo_id: str, access_key: str, timeout: float = 5.0, etag: Optional[str] = None
) -> Optional[Dict]:
    """Fetch live Unsplash photo metadata (minimal subset) or return None on failure.

    Returns a dict with 'data' and 'etag' keys, or None on failure.
    """
    # Record the invocation early to aid debugging when called from a running
    # server process. We intentionally avoid writing the full key value.
    try:
        debug_log(
            "fetch_photo_meta called: photo_id=%s access_key_present=%s timeout=%s"
            % (photo_id, bool(access_key), timeout)
        )
    except Exception:
        pass
    if not photo_id or not access_key:
        return None
    url = f"https://api.unsplash.com/photos/{photo_id}"
    headers = {"Authorization": f"Client-ID {access_key}", "Accept-Version": "v1"}
    if etag:
        headers["If-None-Match"] = etag

    try:
        logger.debug(
            "Fetching Unsplash photo meta: url=%s, photo_id=%s, has_key=%s",
            url,
            photo_id,
            bool(access_key),
        )
        debug_log(
            "fetch_photo_meta: url=%s photo_id=%s timeout=%s" % (url, photo_id, timeout)
        )
        resp = requests.get(url, headers=headers, timeout=timeout)

        # If not 200, log the status and a snippet of the response body
        if resp.status_code == 304:
            # Not modified - return None
            debug_log("fetch_photo_meta: not_modified photo_id=%s" % (photo_id,))
            return None
        elif resp.status_code != 200:
            body = str(getattr(resp, "text", "") or "")
            logger.warning(
                "Unsplash meta fetch failed %s for %s: %s",
                resp.status_code,
                photo_id,
                body[:500],
            )
            debug_log(
                "fetch_photo_meta: status=%s body=%s" % (resp.status_code, body[:1000])
            )
            return None

        try:
            data = resp.json()
        except Exception:
            body = str(getattr(resp, "text", "") or "")
            debug_log("fetch_photo_meta: json_decode_failed body=%s" % (body[:1000],))
            logger.exception("Failed to decode JSON from Unsplash for %s", photo_id)
            return None

        debug_log(
            "fetch_photo_meta: success id=%s keys=%s" % (photo_id, list(data.keys()))
        )

        # Extract ETag from response headers
        response_etag = resp.headers.get("ETag")

        # Trim to needed fields only
        trimmed_data = _trim_photo_data(data)

        # Return both data and etag
        return {"data": trimmed_data, "etag": response_etag}
    except Exception:
        # Log the full exception with traceback at warning level
        logger.exception("Exception fetching Unsplash photo meta for %s", photo_id)
        return None


def fetch_random_photo(
    query: str, access_key: str, timeout: float = 5.0
) -> Optional[Dict]:
    """Fetch a random Unsplash photo for a given query (category) as a live fallback.

    Returns a trimmed object similar to fetch_photo_meta or None on failure.
    """
    if not query or not access_key:
        return None
    url = "https://api.unsplash.com/photos/random"
    headers = {"Authorization": f"Client-ID {access_key}", "Accept-Version": "v1"}
    params = {"query": query, "orientation": "landscape", "content_filter": "high"}
    try:
        debug_log("fetch_random_photo: query=%s url=%s" % (query, url))
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        if resp.status_code != 200:
            body = str(getattr(resp, "text", "") or "")
            logger.warning(
                "Unsplash random fetch failed %s for query=%s: %s",
                resp.status_code,
                query,
                body[:500],
            )
            debug_log(
                "fetch_random_photo: status=%s body=%s"
                % (resp.status_code, body[:1000])
            )
            return None
        data = resp.json()
        # Trim to needed fields only
        return _trim_photo_data(data)
    except Exception:
        logger.exception("Exception fetching Unsplash random photo for query=%s", query)
        return None


async def fetch_photo_meta_async(photo_id: str, access_key: str) -> Optional[Dict]:
    """Async version of fetch_photo_meta using httpx with retry logic."""
    if not photo_id or not access_key:
        return None
    url = f"https://api.unsplash.com/photos/{photo_id}"
    headers = {"Authorization": f"Client-ID {access_key}", "Accept-Version": "v1"}
    try:
        logger.debug(
            "Fetching Unsplash photo meta async: url=%s, photo_id=%s", url, photo_id
        )
        debug_log(f"fetch_photo_meta_async: url={url} photo_id={photo_id}")
        resp = await async_get(url, headers=headers)
        if resp.status_code != 200:
            logger.warning(
                "Unsplash meta fetch failed %s for %s: %s",
                resp.status_code,
                photo_id,
                resp.text[:500],
            )
            debug_log(
                f"fetch_photo_meta_async: status={resp.status_code} "
                f"body={resp.text[:1000]}"
            )
            return None
        try:
            data = resp.json()
        except Exception:
            debug_log(
                f"fetch_photo_meta_async: json_decode_failed "
                f"body={resp.text[:1000]}"
            )
            logger.exception("Failed to decode JSON from Unsplash for %s", photo_id)
            return None
        debug_log(
            f"fetch_photo_meta_async: success id={photo_id} "
            f"keys={list(data.keys())}"
        )
        return _trim_photo_data(data)
    except Exception:
        logger.exception(
            "Exception fetching Unsplash photo meta async for %s", photo_id
        )
        return None


async def fetch_random_photo_async(query: str, access_key: str) -> Optional[Dict]:
    """Async version of fetch_random_photo using httpx with retry logic."""
    if not query or not access_key:
        return None
    url = "https://api.unsplash.com/photos/random"
    headers = {"Authorization": f"Client-ID {access_key}", "Accept-Version": "v1"}
    params = {"query": query, "orientation": "landscape", "content_filter": "high"}
    try:
        debug_log(f"fetch_random_photo_async: query={query} url={url}")
        resp = await async_get(url, headers=headers, params=params)
        if resp.status_code != 200:
            logger.warning(
                "Unsplash random fetch failed %s for query=%s: %s",
                resp.status_code,
                query,
                resp.text[:500],
            )
            debug_log(
                f"fetch_random_photo_async: status={resp.status_code} "
                f"body={resp.text[:1000]}"
            )
            return None
        data = resp.json()
        return _trim_photo_data(data)
    except Exception:
        logger.exception(
            "Exception fetching Unsplash random photo async for query=%s", query
        )
        return None
