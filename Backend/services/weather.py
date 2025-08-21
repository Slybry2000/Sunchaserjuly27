import os
import logging
from tenacity import retry, stop_after_attempt, wait_random, before_sleep_log
from typing import TypedDict, List, Tuple
import httpx
from utils.cache_inproc import InProcessCache
from Backend.models.errors import UpstreamError

# Backwards-compatible alias expected by some tests
class WeatherError(UpstreamError):
    pass


async def get_weather(lat: float, lon: float) -> dict:
    """Compatibility wrapper used by older tests — returns raw provider dict."""
    raw = await fetch_weather_raw(lat, lon)
    return raw

logger = logging.getLogger("weather")

class WeatherSlot(TypedDict):
    ts_local: str
    cloud_pct: int
    temp_f: float

@retry(stop=stop_after_attempt(2), wait=wait_random(min=0.2, max=0.4), before_sleep=before_sleep_log(logger, logging.WARNING))
async def fetch_weather_raw(lat: float, lon: float) -> dict:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=cloudcover,temperature_2m"
        "&temperature_unit=fahrenheit"
        "&timezone=auto"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"Weather upstream error: {e}")
        # Raise for callers that expect an exception, but also allow
        # higher-level callers to handle fallback. Keep the original
        # exception type available as UpstreamError.
        raise UpstreamError(f"Weather provider failed: {e}") from e


# Backwards-compatible alias used in older tests
async def fetch_weather(lat: float, lon: float) -> dict:
    return await fetch_weather_raw(lat, lon)

def parse_weather(payload: dict) -> List[WeatherSlot]:
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    clouds = hourly.get("cloudcover", [])
    temps = hourly.get("temperature_2m", [])
    assert len(times) == len(clouds) == len(temps)
    out: List[WeatherSlot] = []
    for i in range(min(len(times), 48)):
        out.append({
            "ts_local": times[i],
            "cloud_pct": int(clouds[i]),
            "temp_f": float(temps[i]),
        })
    return out

_weather_cache = InProcessCache(maxsize=256, default_ttl=1200, default_swr=600)

async def get_weather_cached(lat: float, lon: float) -> Tuple[List[WeatherSlot], str]:
    key = f"wx:{round(lat,4)}:{round(lon,4)}"
    ttl = int(os.getenv("WEATHER_TTL_SEC","1200"))
    swr = int(os.getenv("WEATHER_STALE_REVAL_SEC","600"))

    async def producer():
        try:
            raw = await fetch_weather_raw(lat, lon)
            return parse_weather(raw)
        except UpstreamError:
            logger.warning("Weather fetch failed, returning empty slots as fallback")
            return []

    value = await _weather_cache.get_or_set(key, producer, ttl, swr)
    return value, "cached"
