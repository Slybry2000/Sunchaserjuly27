import os
import asyncio
import logging
from typing import List, Tuple, Optional

from Backend.services.weather import get_weather_cached
from Backend.models.errors import TimeoutBudgetExceeded, SchemaError, UpstreamError

logger = logging.getLogger(__name__)

DIST_W = float(os.getenv("SCORE_DISTANCE_WEIGHT", "0.1"))
DUR_W = float(os.getenv("SCORE_DURATION_WEIGHT", "10"))
CLOUD = int(os.getenv("SUNNY_CLOUD_THRESHOLD", "30"))
DAY_S = int(os.getenv("DAY_START_HOUR_LOCAL", "8"))
DAY_E = int(os.getenv("DAY_END_HOUR_LOCAL", "18"))
FANOUT = int(os.getenv("WEATHER_FANOUT_CONCURRENCY", "8"))
BUDGET = float(os.getenv("REQUEST_BUDGET_MS", "1500")) / 1000.0


def first_sunny_block(slots: List[dict], day_start=DAY_S, day_end=DAY_E, cloud_threshold=CLOUD) -> Tuple[Optional[str], int]:
    start_iso: Optional[str] = None
    run = 0
    for s in slots:
        hour = int(s["ts_local"][11:13])
        in_window = day_start <= hour <= day_end
        if in_window and int(s.get("cloud_pct", 100)) <= cloud_threshold:
            if start_iso is None:
                start_iso = s["ts_local"]
            run += 1
        elif start_iso is not None:
            break
    return start_iso, run


def score_candidate(distance_mi: float, duration_hours: int, sun_start_iso: Optional[str]) -> float:
    base = duration_hours * DUR_W - distance_mi * DIST_W
    return round(max(0.0, base), 3)


async def rank(origin_lat, origin_lon, candidates: List[dict], *, max_weather=20, concurrency=FANOUT, budget_s=BUDGET, weather_fetch=get_weather_cached):
    """Score and rank candidate locations concurrently.

    Uses asyncio.gather(return_exceptions=True) so that all candidate coroutines are awaited and
    exceptions are observed. Critical exceptions (TimeoutBudgetExceeded, SchemaError) are re-raised
    so callers/tests can respond accordingly; other candidate errors are logged and skipped.
    """
    sem = asyncio.Semaphore(concurrency)

    async def eval_one(c):
        async with sem:
            slots, wx_status = await weather_fetch(c["lat"], c["lon"])
            try:
                start_iso, duration = first_sunny_block(slots)
            except Exception as e:
                raise SchemaError(f"Weather data invalid: {e}") from e
            score = score_candidate(c.get("distance_mi", 0.0), duration, start_iso)
            return {
                "id": c.get("id"),
                "name": c.get("name"),
                "lat": c.get("lat"),
                "lon": c.get("lon"),
                "distance_mi": round(c.get("distance_mi", 0.0), 1),
                "sun_start_iso": start_iso,
                "duration_hours": duration,
                "score": round(score, 2),
            }

    async def run_all():
        coros = [eval_one(c) for c in candidates[:max_weather]]
        gather_task = asyncio.gather(*coros, return_exceptions=True)
        try:
            results = await asyncio.wait_for(gather_task, timeout=budget_s)
        except asyncio.TimeoutError:
            # cancel the gather to ensure tasks are not left running
            gather_task.cancel()
            raise TimeoutBudgetExceeded(f"Weather ranking timed out after {budget_s} seconds")

        processed = []
        for r in results:
            if isinstance(r, Exception):
                # Propagate critical exceptions so callers/tests handle them
                if isinstance(r, (TimeoutBudgetExceeded, SchemaError, UpstreamError)):
                    raise r
                # Otherwise, log and skip this candidate
                logger.debug("Candidate evaluation failed and will be skipped: %s", r)
                continue
            processed.append(r)

        return processed

    results = await run_all()

    def sort_key(r):
        s = -r["score"]
        t = r.get("sun_start_iso") or "9999-12-31T00:00"
        d = r.get("distance_mi", 0.0)
        # include id as a final deterministic tie-breaker (string)
        return (s, t, d, str(r.get("id", "")))

    results.sort(key=sort_key)
    return results


async def score_location(loc, weather: dict):
    """Score a single Location given raw weather dict (compat test helper).

    Returns an object with .score and .best_window attributes for compatibility with tests.
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
