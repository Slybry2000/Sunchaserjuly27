import asyncio
import json
from pathlib import Path
import pytest

from services.weather import parse_weather

FIXTURE_DIR = Path(__file__).resolve().parents[1] / 'fixtures'
FIXTURE = FIXTURE_DIR / 'open_meteo_hourly.json'

@pytest.mark.asyncio
async def test_parse_fixture_and_score():
    data = json.loads(FIXTURE.read_text(encoding='utf-8'))
    slots = parse_weather(data)
    assert isinstance(slots, list)
    assert len(slots) > 0
    # simple sanity checks on slot fields
    s = slots[0]
    assert 'ts_local' in s and 'cloud_pct' in s and 'temp_f' in s

    # compute simple score
    next24 = slots[:24]
    sunny = sum(1 for sl in next24 if sl['cloud_pct'] <= 30)
    score = sunny / len(next24)
    assert 0.0 <= score <= 1.0
