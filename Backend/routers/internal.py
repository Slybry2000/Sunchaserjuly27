import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from Backend.utils.geo import haversine_miles

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUT_JSON = DATA_DIR / "forecast_snapshot.json"
OUT_DB = DATA_DIR / "forecast_snapshot.db"


def _read_db() -> List[Dict]:
    if not OUT_DB.exists():
        return []
    conn = sqlite3.connect(str(OUT_DB))
    cur = conn.cursor()
    cur.execute(
        "SELECT lat, lon, score, slots_count, generated_at FROM snapshots ORDER BY id"
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "lat": r[0],
            "lon": r[1],
            "score": r[2],
            "slots_count": r[3],
            "generated_at": r[4],
        }
        for r in rows
    ]


def _read_json() -> List[Dict]:
    if not OUT_JSON.exists():
        return []
    return json.loads(OUT_JSON.read_text(encoding="utf-8"))


@router.get("/internal/forecasts")
async def get_forecasts(
    lat: Optional[float] = Query(None, description="Latitude to filter by"),
    lon: Optional[float] = Query(None, description="Longitude to filter by"),
    radius: Optional[float] = Query(None, description="Radius in miles to filter by"),
    top: int = Query(10, ge=1, le=100, description="Top N results to return"),
):
    # Load snapshots (prefer DB)
    items = _read_db() or _read_json()
    if not items:
        raise HTTPException(status_code=404, detail="No forecast snapshot available")

    # If lat/lon provided, compute distance and filter
    if lat is not None and lon is not None:
        for it in items:
            try:
                it["distance_mi"] = round(
                    haversine_miles(lat, lon, float(it["lat"]), float(it["lon"])), 1
                )
            except Exception:
                it["distance_mi"] = None

        if radius is not None:
            items = [
                it
                for it in items
                if it.get("distance_mi") is not None and it["distance_mi"] <= radius
            ]

    # Sort by score desc, then distance asc (None distances sort last)
    def sort_key(it):
        dist = (
            it.get("distance_mi") if it.get("distance_mi") is not None else float("inf")
        )
        return (-float(it.get("score", 0)), dist)

    items = sorted(items, key=sort_key)
    items = items[:top]

    source = "sqlite" if OUT_DB.exists() else "json"
    return {"source": source, "count": len(items), "items": items}
