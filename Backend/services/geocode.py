"""
Geocoding service using Mapbox API
"""

import os
from typing import Any, Mapping

import httpx

from Backend.models.errors import LocationNotFound


async def geocode(query: str) -> tuple[float, float]:
    """
    Geocode a location query using Mapbox API

    Args:
        query: Location query string (e.g., "Seattle, WA")

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        LocationNotFound: If no location is found
    """
    mapbox_token = os.getenv("MAPBOX_TOKEN")
    if not mapbox_token:
        # Development convenience: allow a small local mapping when explicitly enabled.
        dev_allow = os.getenv("DEV_ALLOW_GEOCODE", "").lower() in ("1", "true", "yes")
        if dev_allow:
            # Small mapping for common test queries (kept intentionally tiny).
            fallback = {
                "seattle": (47.6062, -122.3321),
                "seattle, wa": (47.6062, -122.3321),
                "portland": (45.5152, -122.6784),
                "portland, or": (45.5152, -122.6784),
                "renton": (47.4829, -122.2171),
                "renton, wa": (47.4829, -122.2171),
            }
            qnorm = query.strip().lower()
            if qnorm in fallback:
                return fallback[qnorm]
            raise LocationNotFound(f"Dev geocode: no mapping for query: {query}")
        raise ValueError("MAPBOX_TOKEN environment variable not set")

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    params: Mapping[str, Any] = {"access_token": mapbox_token, "limit": 1}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if not data.get("features"):
                raise LocationNotFound(f"No location found for query: {query}")

            feature = data["features"][0]
            coordinates = feature["geometry"]["coordinates"]

            # Mapbox returns [longitude, latitude]
            longitude, latitude = coordinates
            return latitude, longitude

        except httpx.RequestError as e:
            raise LocationNotFound(f"Geocoding request failed: {e}") from e
        except httpx.HTTPStatusError as e:
            raise LocationNotFound(
                f"Geocoding API error: {e.response.status_code}"
            ) from e
