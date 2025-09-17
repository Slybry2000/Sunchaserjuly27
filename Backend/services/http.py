from typing import Optional

import httpx

_shared_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None:
        _shared_client = httpx.AsyncClient()
    return _shared_client


async def close_http_client():
    global _shared_client
    if _shared_client is not None:
        await _shared_client.aclose()
        _shared_client = None
