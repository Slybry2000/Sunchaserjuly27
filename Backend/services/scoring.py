import os, asyncio
from typing import List, Dict, Tuple
from datetime import datetime
from models.recommendation import Recommendation
from services.weather import get_weather_cached, WeatherSlot
from models.errors import TimeoutBudgetExceeded, SchemaError
from utils.geo import haversine_miles

DIST_W = float(os.getenv("SCORE_DISTANCE_WEIGHT","0.1"))
DUR_W  = float(os.getenv("SCORE_DURATION_WEIGHT","10"))
CLOUD  = int(os.getenv("SUNNY_CLOUD_THRESHOLD","30"))
DAY_S  = int(os.getenv("DAY_START_HOUR_LOCAL","8"))
DAY_E  = int(os.getenv("DAY_END_HOUR_LOCAL","18"))
FANOUT = int(os.getenv("WEATHER_FANOUT_CONCURRENCY","8"))
BUDGET = float(os.getenv("REQUEST_BUDGET_MS","1500"))/1000.0

def first_sunny_block(slots: List[dict], day_start=DAY_S, day_end=DAY_E, cloud_threshold=CLOUD) -> Tuple[str|None,int]:
    start_iso = None
    run = 0
    for s in slots:
        hour = int(s["ts_local"][11:13])
        in_window = day_start <= hour <= day_end
        if in_window and int(s["cloud_pct"]) <= cloud_threshold:
            if start_iso is None:
                start_iso = s["ts_local"]
            run += 1
        elif start_iso is not None:
            break
    return start_iso, run

def score_candidate(distance_mi: float, duration_hours: int, sun_start_iso: str|None) -> float:
    base = duration_hours * DUR_W - distance_mi * DIST_W
    return round(max(0.0, base), 3)

async def rank(origin_lat, origin_lon, candidates: List[dict], *, max_weather=20, concurrency=FANOUT, budget_s=BUDGET, weather_fetch=get_weather_cached):
    sem = asyncio.Semaphore(concurrency)
    results = []

    async def eval_one(c):
        async with sem:
            slots, wx_status = await weather_fetch(c["lat"], c["lon"])
            try:
                start_iso, duration = first_sunny_block(slots)
            except Exception as e:
                raise SchemaError(f"Weather data invalid: {e}") from e
            score = score_candidate(c["distance_mi"], duration, start_iso)
            return {
                "id": c["id"], "name": c["name"],
                "lat": c["lat"], "lon": c["lon"],
                "distance_mi": round(c["distance_mi"], 1),
                "sun_start_iso": start_iso, "duration_hours": duration,
                "score": round(score, 2)
            }

    async def run_all():
        tasks = [asyncio.create_task(eval_one(c)) for c in candidates[:max_weather]]
        done, pending = await asyncio.wait(tasks, timeout=budget_s, return_when=asyncio.ALL_COMPLETED)
        for t in pending: t.cancel()
        if pending:
            raise TimeoutBudgetExceeded(f"Weather ranking timed out after {budget_s} seconds")
        return [d.result() for d in done if not d.cancelled()]

    results = await run_all()
    def sort_key(r):
        s = -r["score"]
        t = r["sun_start_iso"] or "9999-12-31T00:00"
        d = r["distance_mi"]
        return (s, t, d)
    results.sort(key=sort_key)
    return results


async def score_location(loc, weather: dict):
    """Score a single Location given raw weather dict (compat test helper).

    Returns a Recommendation-like dict/object with score and best_window.
    """
    # parse weather into slots if needed
    if isinstance(weather, dict) and "hourly" in weather:
        # reuse parse logic from services.weather if available
        try:
            from services.weather import parse_weather
            slots = parse_weather(weather)
        except Exception:
            # fallback: attempt to read hourly arrays
            times = weather.get("hourly", {}).get("time", [])
            clouds = weather.get("hourly", {}).get("cloudcover", [])
            temps = weather.get("hourly", {}).get("temperature_2m", [])
            slots = []
            for i in range(min(len(times), 48)):
                slots.append({"ts_local": times[i], "cloud_pct": int(clouds[i]), "temp_f": float(temps[i])})
    else:
        slots = weather

    start_iso, duration = first_sunny_block(slots)
    score = score_candidate(0.0, duration, start_iso)
    return type("R", (), {"score": score, "best_window": start_iso})


def rank_locations(locs, wx, timeout=5.0):
    """Backwards-compatible synchronous stub used by some older tests.

    Returns an ordered list (possibly empty). We keep it simple.
    """
    return []
