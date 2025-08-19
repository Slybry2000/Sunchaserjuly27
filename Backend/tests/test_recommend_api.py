import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

client = TestClient(app)

def test_recommend_happy_path():
    with patch('services.weather.get_weather_cached') as mock_weather:
        mock_weather.return_value = ([
            {"ts_local": "2025-08-11T12:00", "temp_f": 72.0, "cloud_pct": 20}
        ], "cached")
        
        resp = client.get("/recommend?lat=47.6&lon=-122.3")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)

def test_recommend_radius_clamp():
    with patch('services.weather.get_weather_cached') as mock_weather:
        mock_weather.return_value = ([
            {"ts_local": "2025-08-11T12:00", "temp_f": 72.0, "cloud_pct": 20}
        ], "cached")
        
        resp = client.get("/recommend?lat=47.6&lon=-122.3&radius=1000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"]["radius"] <= 300

def test_recommend_q_disabled():
    resp = client.get("/recommend?q=Seattle")
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "geocoding_disabled"
