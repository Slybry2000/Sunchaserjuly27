import math
from typing import Tuple


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (km)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def haversine_miles(lat1, lon1, lat2, lon2) -> float:
    R = 3958.7613
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def bbox_degrees(lat, lon, radius_mi) -> tuple[float, float, float, float]:
    # returns (min_lat, min_lon, max_lat, max_lon) approximate box
    dlat = radius_mi / 69.0
    dlon = radius_mi / (
        69.172 * max(0.1, math.cos(math.radians(lat)))
    )
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def clamp_bbox(
    lat: float, lon: float, radius_km: float
) -> Tuple[float, float, float, float]:
    """Return bounding box (min_lat, min_lon, max_lat, max_lon) for radius (km)."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * math.cos(math.radians(lat)))
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)


def normalize_latlon(lat: float, lon: float) -> Tuple[float, float]:
    """Clamp latitude and longitude to valid ranges."""
    lat = max(-90.0, min(90.0, lat))
    lon = ((lon + 180) % 360) - 180
    return lat, lon
