"""
Geocoding service using Mapbox API
"""
import os

import httpx


class LocationNotFound(Exception):
    """Raised when geocoding fails to find a location"""
    pass


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
        raise ValueError("MAPBOX_TOKEN environment variable not set")

    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    params = {
        "access_token": mapbox_token,
        "limit": 1
    }

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
            raise LocationNotFound(f"Geocoding API error: {e.response.status_code}") from e
