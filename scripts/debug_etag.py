import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from Backend.main import app
from routers.recommend import get_weather_dep

async def fake_weather(lat, lon):
    slots = [{'ts_local': f'2025-08-18T{str(i).zfill(2)}:00', 'cloud_pct': 10, 'temp_f': 65} for i in range(24)]
    return slots, 'hit_fresh'

app.dependency_overrides[get_weather_dep] = lambda: fake_weather
client = TestClient(app)
resp = client.get('/recommend?lat=47.6&lon=-122.3&radius=100')
print('first status', resp.status_code)
print('first ETag:', resp.headers.get('ETag'))
print('first body keys:', list(resp.json().keys()) if resp.status_code==200 else None)

etag = resp.headers.get('ETag')
resp2 = client.get('/recommend?lat=47.6&lon=-122.3&radius=100', headers={'If-None-Match': etag})
print('second status', resp2.status_code)
print('second ETag:', resp2.headers.get('ETag'))
print('second body keys:', list(resp2.json().keys()) if resp2.status_code==200 else None)
