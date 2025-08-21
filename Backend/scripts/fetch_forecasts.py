import asyncio
import json
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from Backend.services.weather import get_weather_cached

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
PNW_CSV = DATA_DIR / 'pnw.csv'
OUT_JSON = DATA_DIR / 'forecast_snapshot.json'
OUT_DB = DATA_DIR / 'forecast_snapshot.db'


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


def _init_db(path: Path):
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            score REAL NOT NULL,
            slots_count INTEGER NOT NULL,
            generated_at TEXT NOT NULL
        )
        '''
    )
    conn.commit()
    return conn


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

    # ensure output directory exists
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    # write JSON snapshot (same as before)
    with open(OUT_JSON, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, indent=2)

    # persist to SQLite for local/dev consumption
    conn = _init_db(OUT_DB)
    cur = conn.cursor()
    # simple approach: delete previous run and insert fresh rows
    cur.execute('DELETE FROM snapshots')
    now = datetime.now(timezone.utc).isoformat()
    rows = [(r['lat'], r['lon'], r['score'], r['slots_count'], now) for r in results]
    if rows:
        cur.executemany(
            'INSERT INTO snapshots (lat, lon, score, slots_count, generated_at) VALUES (?, ?, ?, ?, ?)',
            rows,
        )
    conn.commit()
    conn.close()

    print(f'Wrote {len(results)} snapshots to {OUT_JSON} and persisted to {OUT_DB}')


if __name__ == '__main__':
    asyncio.run(main())
