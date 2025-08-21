"""
Tests for geocoding endpoint
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_geocode_endpoint_success():
    """Test successful geocoding endpoint"""
    with patch('main.geocode') as mock_geocode:
        mock_geocode.return_value = (47.6061, -122.3328)

        response = client.get("/geocode?q=Seattle")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Seattle"
        assert data["lat"] == 47.6061
        assert data["lon"] == -122.3328


def test_geocode_endpoint_not_found():
    """Test geocoding endpoint with location not found"""
    with patch('main.geocode') as mock_geocode:
        from Backend.services.geocode import LocationNotFound
        mock_geocode.side_effect = LocationNotFound("No location found")

        response = client.get("/geocode?q=nonexistent")

        assert response.status_code == 404
        assert "No location found" in response.json()["detail"]


def test_geocode_endpoint_missing_query():
    """Test geocoding endpoint without query parameter"""
    response = client.get("/geocode")

    assert response.status_code == 422  # Validation error
