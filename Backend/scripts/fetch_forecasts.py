import asyncio
import json
import csv
from pathlib import Path
from services.weather import get_weather_cached, parse_weather

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
PNW_CSV = DATA_DIR / 'pnw.csv'
OUT_JSON = DATA_DIR / 'forecast_snapshot.json'

async def fetch_for_location(lat: float, lon: float):
    slots, status = await get_weather_cached(lat, lon)
    # compute simple sun confidence: percent of next 24 hours with cloud_pct <= 30
    next24 = slots[:24]
    if not next24:
        score = 0.0
    else:
        sunny = sum(1 for s in next24 if s['cloud_pct'] <= 30)
        score = sunny / len(next24)
    return {
        'lat': lat,
        'lon': lon,
        'score': round(score, 3),
        'slots_count': len(slots),
    }

async def main(limit=100):
    locs = []
    with open(PNW_CSV, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
                locs.append((lat, lon))
            except Exception:
                continue

    results = []
    sem = asyncio.Semaphore(8)

    async def _run(lat, lon):
        async with sem:
            return await fetch_for_location(lat, lon)

    tasks = [asyncio.create_task(_run(lat, lon)) for lat, lon in locs]
    for coro in asyncio.as_completed(tasks):
        res = await coro
        results.append(res)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, indent=2)

    print(f'Wrote {len(results)} snapshots to {OUT_JSON}')

if __name__ == '__main__':
    asyncio.run(main())
