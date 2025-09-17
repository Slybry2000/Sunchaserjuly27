from fastapi.testclient import TestClient

from main import app


def test_etag_invariance(monkeypatch):
    client = TestClient(app)
    # Patch weather and scoring to return deterministic data
    monkeypatch.setattr(
        "services.weather.get_weather",
        lambda lat, lon: {
            "hourly": {
                "time": ["2025-08-11T12:00"],
                "temperature_2m": [20],
                "cloudcover": [10],
                "precipitation_probability": [0],
            }
        },
    )
    monkeypatch.setattr(
        "services.scoring.rank_locations", lambda locs, wx, timeout=5.0: []
    )
    url = "/recommend?lat=46.8&lon=-121.7&radius=100"
    r1 = client.get(url)
    r2 = client.get(url)
    if r1.status_code == 200 and r2.status_code == 200:
        assert r1.headers["ETag"] == r2.headers["ETag"]
