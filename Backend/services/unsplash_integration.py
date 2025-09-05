"""Small helpers for Unsplash integration.

Provides:
- trigger_photo_download(download_location, access_key): calls Unsplash download endpoint
- build_attribution_html(photo): returns a small HTML snippet for attribution links

These are intentionally small and dependency-light so they can be used from both
API handlers and background tasks.
"""
from typing import Dict
import logging

import requests

logger = logging.getLogger(__name__)


def trigger_photo_download(download_location: str, access_key: str, timeout: float = 5.0) -> bool:
    """Trigger Unsplash "download" endpoint for tracking photo usage.

    Args:
        download_location: the photo.links.download_location string returned by Unsplash.
        access_key: Unsplash Client ID (not a secret in the same sense as private keys).
        timeout: request timeout in seconds.

    Returns:
        True if the request succeeded (2xx/3xx), False otherwise.

    Notes:
        This function performs a GET request to the provided download_location and
        attaches the required Authorization header per Unsplash guidelines.
    """
    if not download_location or not access_key:
        logger.debug("trigger_photo_download called with empty download_location or access_key")
        return False

    headers = {"Authorization": f"Client-ID {access_key}"}
    try:
        resp = requests.get(download_location, headers=headers, timeout=timeout)
        logger.debug("Unsplash download tracking response: %s %s", resp.status_code, getattr(resp, 'text', None))
        # Treat 2xx and reasonable redirects (3xx) as success
        return 200 <= resp.status_code < 400
    except Exception as exc:
        # Accept any exception here so callers get a boolean result instead of
        # an exception. Network libraries can raise various exceptions and
        # tests may mock generic Exceptions.
        logger.warning("Failed to call Unsplash download endpoint: %s", exc)
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
        f'Photo by <a href="{user_link}" rel="nofollow noopener noreferrer" target="_blank">'
        f"{user_name}</a> on <a href=\"{photo_link}\" rel=\"nofollow noopener noreferrer\" target=\"_blank\">Unsplash</a>"
    )
