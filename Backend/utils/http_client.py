import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Global async client for connection reuse
_client: Optional[httpx.AsyncClient] = None


def get_async_client() -> httpx.AsyncClient:
    """Get or create the global async HTTP client."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
            headers={"Accept-Version": "v1"},
        )
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)
    ),
    reraise=True,
)
async def async_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> httpx.Response:
    """Async GET request with retry logic for transient failures."""
    client = get_async_client()
    try:
        response = await client.get(url, headers=headers, params=params)
        # Handle rate limiting with a simple retry
        if response.status_code == 429:
            logger.warning("Rate limited by Unsplash API, retrying...")
            raise httpx.HTTPStatusError(
                "Rate limited", request=response.request, response=response
            )
        return response
    except Exception as e:
        logger.exception("HTTP request failed: %s", e)
        raise


async def close_client():
    """Close the global async client (call on shutdown)."""
    global _client
    if _client:
        await _client.aclose()
        _client = None
