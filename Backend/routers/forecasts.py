from fastapi import APIRouter, HTTPException, Query, Header, Response
from pathlib import Path
import json
import sqlite3
from typing import List, Dict, Optional

from utils.geo import haversine_miles
from utils.etag import strong_etag_for_obj

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
OUT_JSON = DATA_DIR / 'forecast_snapshot.json'
OUT_DB = DATA_DIR / 'forecast_snapshot.db'


def _read_db() -> List[Dict]:
    if not OUT_DB.exists():
        return []
    conn = sqlite3.connect(str(OUT_DB))
    cur = conn.cursor()
    cur.execute('SELECT lat, lon, score, slots_count, generated_at FROM snapshots ORDER BY id')
    rows = cur.fetchall()
    conn.close()
    return [
        {
            'lat': r[0],
            'lon': r[1],
            'score': r[2],
            'slots_count': r[3],
            'generated_at': r[4],
        }
        for r in rows
    ]


def _read_json() -> List[Dict]:
    if not OUT_JSON.exists():
        return []
    return json.loads(OUT_JSON.read_text(encoding='utf-8'))


def _prepare_items(items, lat: Optional[float], lon: Optional[float], radius: Optional[float], top: int):
    if lat is not None and lon is not None:
        for it in items:
            try:
                it['distance_mi'] = round(haversine_miles(lat, lon, float(it['lat']), float(it['lon'])), 1)
            except Exception:
                it['distance_mi'] = None

        if radius is not None:
            items = [it for it in items if it.get('distance_mi') is not None and it['distance_mi'] <= radius]

    # Sort by score desc, then distance asc (None distances sort last)
    def sort_key(it):
        dist = it.get('distance_mi') if it.get('distance_mi') is not None else float('inf')
        return (-float(it.get('score', 0)), dist)

    items = sorted(items, key=sort_key)
    items = items[:top]
    return items


@router.get('/forecasts')
async def public_forecasts(
    response: Response,
    lat: Optional[float] = Query(None, description='Latitude to filter by'),
    lon: Optional[float] = Query(None, description='Longitude to filter by'),
    radius: Optional[float] = Query(None, description='Radius in miles to filter by'),
    top: int = Query(10, ge=1, le=100, description='Top N results to return'),
    if_none_match: Optional[str] = Header(None, convert_underscores=False),
):
    items = _read_db() or _read_json()
    if not items:
        raise HTTPException(status_code=404, detail='No forecast snapshot available')

    filtered = _prepare_items(items, lat, lon, radius, top)

    payload = {'source': 'sqlite' if OUT_DB.exists() else 'json', 'count': len(filtered), 'items': filtered}
    # Compute ETag from canonical JSON (stable ordering)
    # Use object-level canonicalization for consistent ETag generation
    etag = strong_etag_for_obj(payload)

    # Honor If-None-Match
    if if_none_match is not None and if_none_match == etag:
        response.status_code = 304
        response.headers['ETag'] = etag
        return None

    response.headers['ETag'] = etag
    response.headers['Cache-Control'] = 'public, max-age=30'
    return payload
