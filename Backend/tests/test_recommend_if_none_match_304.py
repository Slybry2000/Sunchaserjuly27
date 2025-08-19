from fastapi.testclient import TestClient
from main import app
from datetime import datetime

client = TestClient(app)

def test_if_none_match_returns_304(monkeypatch):
    url = "/recommend?lat=47.6&lon=-122.3"
    # Patch weather to avoid real HTTP calls and make scoring deterministic
    async def fake_get_weather_cached(lat, lon):
        slots = [{"ts_local": "2025-08-14T09:00", "cloud_pct": 10, "temp_f": 68.0}]
        return slots, "hit_fresh"

    # Patch both the implementation and any already-imported references
    monkeypatch.setattr("services.weather.get_weather_cached", fake_get_weather_cached)
    monkeypatch.setattr("services.scoring.get_weather_cached", fake_get_weather_cached)

    # Freeze the generated_at timestamp used by RecommendResponse so the ETag is stable
    fixed_dt = datetime(2025, 8, 14, 12, 0, 0)
    class FakeDatetime:
        @staticmethod
        def utcnow():
            return fixed_dt

    monkeypatch.setattr("models.recommendation.datetime", FakeDatetime)

    # First request to get an ETag
    r1 = client.get(url)
    assert r1.status_code == 200
    etag = r1.headers.get("ETag")
    assert etag is not None

    # Second request with If-None-Match header
    r2 = client.get(url, headers={"If-None-Match": etag})
    assert r2.status_code == 304
    # ETag should still be present
    assert r2.headers.get("ETag") == etag
