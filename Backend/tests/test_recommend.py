from fastapi.testclient import TestClient
from main import app

def test_recommend_happy(monkeypatch):
    client = TestClient(app)
    # Patch weather and scoring to avoid real HTTP
    monkeypatch.setattr("services.weather.get_weather", lambda lat, lon: {"hourly": {"time": ["2025-08-11T12:00"], "temperature_2m": [20], "cloudcover": [10], "precipitation_probability": [0]}})
    monkeypatch.setattr("services.scoring.rank_locations", lambda locs, wx, timeout=5.0: [])
    response = client.get("/recommend?lat=46.8&lon=-121.7&radius=100")
    assert response.status_code in (200, 404)  # 404 if no locations in radius
    if response.status_code == 200:
        assert "ETag" in response.headers
        assert "recommendations" in response.json()

def test_recommend_missing_param():
    client = TestClient(app)
    response = client.get("/recommend?lat=46.8")
    assert response.status_code == 422
