import pytest
import asyncio
from models.recommendation import Location
from services.scoring import score_location

@pytest.mark.asyncio
async def test_score_location_sunny():
    loc = Location(id=1, name="Test", lat=0, lon=0, elevation=0, category="Test", state="TS", timezone="UTC")
    weather = {
        "hourly": {
            "time": ["2025-08-11T12:00"],
            "temperature_2m": [20],
            "cloudcover": [10],
            "precipitation_probability": [0]
        }
    }
    rec = await score_location(loc, weather)
    assert rec.score > 0
    assert rec.best_window is not None

@pytest.mark.asyncio
async def test_score_location_no_sun():
    loc = Location(id=1, name="Test", lat=0, lon=0, elevation=0, category="Test", state="TS", timezone="UTC")
    weather = {
        "hourly": {
            "time": ["2025-08-11T12:00"],
            "temperature_2m": [10],
            "cloudcover": [90],
            "precipitation_probability": [50]
        }
    }
    rec = await score_location(loc, weather)
    assert rec.score == 0
    assert rec.best_window is None
