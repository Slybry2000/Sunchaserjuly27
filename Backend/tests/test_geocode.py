"""
Tests for geocoding service
"""

from unittest.mock import patch

import pytest

from Backend.services.geocode import LocationNotFound, geocode


@pytest.mark.asyncio
async def test_geocode_success(httpx_mock):
    """Test successful geocoding"""
    # Mock Mapbox API response
    mock_response = {
        "features": [
            {
                "geometry": {
                    "coordinates": [
                        -122.3328,
                        47.6061,
                    ]  # [longitude, latitude] for Seattle
                }
            }
        ]
    }

    url = (
        "https://api.mapbox.com/geocoding/v5/mapbox.places/Seattle, WA.json"
        "?access_token=test_token&limit=1"
    )
    httpx_mock.add_response(url=url, json=mock_response)

    with patch.dict("os.environ", {"MAPBOX_TOKEN": "test_token"}):
        lat, lon = await geocode("Seattle, WA")

        assert lat == 47.6061
        assert lon == -122.3328


@pytest.mark.asyncio
async def test_geocode_not_found(httpx_mock):
    """Test geocoding with no results"""
    mock_response = {"features": []}

    url = (
        "https://api.mapbox.com/geocoding/v5/mapbox.places/nonexistent place.json"
        "?access_token=test_token&limit=1"
    )
    httpx_mock.add_response(url=url, json=mock_response)

    with patch.dict("os.environ", {"MAPBOX_TOKEN": "test_token"}):
        with pytest.raises(LocationNotFound):
            await geocode("nonexistent place")


@pytest.mark.asyncio
async def test_geocode_missing_token():
    """Test geocoding without API token"""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(
            ValueError, match="MAPBOX_TOKEN environment variable not set"
        ):
            await geocode("Seattle, WA")
