import sys
from pathlib import Path

# ensure repo root on path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from Backend.main import app  # noqa: E402


async def fake_weather(lat, lon):
    # deterministic minimal slots: always 24 slots with cloud_pct=10
    slots = [{'ts_local': f'2025-08-18T{str(i).zfill(2)}:00', 'cloud_pct': 10, 'temp_f': 65} for i in range(24)]
    return slots, 'hit_fresh'


def test_if_none_match_304():
    client = TestClient(app)

    # inject dependency using FastAPI's dependency_overrides (consistent with other tests)
    from routers.recommend import get_weather_dep
    app.dependency_overrides[get_weather_dep] = lambda: fake_weather

    # first request to get ETag (use larger radius so candidates are found)
    resp = client.get('/recommend?lat=47.6&lon=-122.3&radius=100')
    assert resp.status_code == 200
    etag = resp.headers.get('ETag')
    assert etag is not None

    # second request with If-None-Match should return 304
    resp2 = client.get('/recommend?lat=47.6&lon=-122.3&radius=100', headers={'If-None-Match': etag})
    assert resp2.status_code == 304
    app.dependency_overrides = {}
