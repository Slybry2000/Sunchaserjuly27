import pytest

from Backend.services.weather import get_weather


@pytest.mark.asyncio
async def test_get_weather(monkeypatch):
    # Patch fetch_weather to avoid real HTTP call
    async def fake_fetch_weather(lat, lon):
        return {
            "hourly": {
                "temperature_2m": [20, 21],
                "cloudcover": [10, 20],
                "precipitation_probability": [0, 0],
            }
        }

    monkeypatch.setattr("services.weather.fetch_weather", fake_fetch_weather)
    result = await get_weather(47.6, -122.3)
    assert "hourly" in result
    assert "temperature_2m" in result["hourly"]
