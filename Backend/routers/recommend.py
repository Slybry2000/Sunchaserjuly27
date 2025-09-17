import json
import os
import re
from hashlib import blake2b

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, Response

from Backend.models.errors import ErrorPayload
from Backend.models.errors import UpstreamError as WeatherError
from Backend.models.recommendation import Recommendation, RecommendResponse
from Backend.services.locations import nearby
from Backend.services.scoring import rank
from Backend.utils.etag import strong_etag_for_obj

# Minimal category -> Unsplash API photo ids for attribution (frontend has a
# broader pool)
# NOTE: These are real Unsplash API photo IDs (not CDN filename fragments).
# They enable live meta fetch and proper attribution. They are generic examples
# and may not perfectly match each category visually until curated.
# Curated PNW-focused Unsplash API photo IDs per category.
# Note: These are public photo IDs extracted from Unsplash photo URLs (the
# trailing token in /photos/<slug>-<id>). They bias selections toward the
# Pacific Northwest to reduce mismatches when we fetch live meta.
CATEGORY_API_IDS = {
    # Dense evergreens, PNW forest mood
    "forest": ["jNmXsyp1Bl0", "Lu8AoWCXATg"],
    # Columbia River Gorge waterfalls/views
    "gorge": ["zIye2BBW6DU"],
    # Oregon Coast beaches and sea stacks
    "beach": ["wb2UdxVof_g"],
    # Local lakes: Lake Washington and iconic Crater Lake
    "lake": ["OV7iMdaAJTg", "J5B1NDtaH50", "67oRvO9Z57s"],
    # Mount Hood classic reflections
    "mountain": ["Re-iyBoo8aQ", "Lu8AoWCXATg"],
    # Snoqualmie Valley / misty foothills
    "valley": ["Lu8AoWCXATg"],
    # Seattle/PNW parks
    "urban park": ["GCo3fo6UZ1U", "HFJ65-zt5s4"],
    "park": ["GCo3fo6UZ1U", "HFJ65-zt5s4"],
    # San Juan Islands seascapes
    "island": ["TGKHFFHRM80"],
    # Smith Rock climbing, Central Oregon
    "climbing": ["ojjc5uA4lCI", "oMjnWW5vjRI"],
    # PNW trail aesthetic
    "trail": ["PSYVXvAitAQ"],
    # Eastern Washington desert/badlands
    "desert": ["1v__2MdOPWU"],
}


def _choose_photo_id(loc_id: str, category: str) -> str | None:
    pool = CATEGORY_API_IDS.get(category.lower().strip())
    if not pool:
        return None
    # Deterministic index based on id so the same location stays stable
    h = blake2b(loc_id.encode("utf-8"), digest_size=2).digest()
    idx = int.from_bytes(h, "big") % len(pool)
    return pool[idx]


_name_suffix_re = re.compile(r"_(\d+)$")


def _clean_name(name: str) -> str:
    """Remove trailing _<digits> from a location name (e.g. 'Park_102' -> 'Park')."""
    return _name_suffix_re.sub("", name or "")


def _choose_photo_id_unique(loc_id: str, category: str, used: set[str]) -> str | None:
    pool = CATEGORY_API_IDS.get(category.lower().strip())
    if not pool:
        return None
    h = blake2b(loc_id.encode("utf-8"), digest_size=2).digest()
    start = int.from_bytes(h, "big") % len(pool)
    for i in range(len(pool)):
        cand = pool[(start + i) % len(pool)]
        if cand not in used:
            used.add(cand)
            return cand
    # All taken; fall back to deterministic
    return pool[start]


router = APIRouter()
ENABLE_Q = os.getenv("ENABLE_Q", "false").lower() == "true"


def get_weather_dep():
    """Dependency provider for weather fetch function; tests override this."""
    return None


@router.get(
    "/recommend",
    response_model=RecommendResponse,
    summary="Get sunshine location recommendations",
    tags=["recommendations"],
    description=(
        "Get sunshine recommendations for coordinates based on weather forecasts. "
        "Returns ranked locations with metadata and supports ETag caching."
    ),
    responses={
        200: {
            "description": "Successful recommendation response with ranked locations",
            "content": {
                "application/json": {
                    "example": {"query": {"lat": 47.6, "lon": -122.3}, "results": []}
                }
            },
        },
        304: {"description": "Not Modified - ETag match"},
        400: {"description": "Bad Request - invalid parameters"},
        422: {"description": "Unprocessable Entity - missing required coordinates"},
        502: {"description": "Bad Gateway - weather service unavailable"},
        504: {"description": "Gateway Timeout - request exceeded time budget"},
    },
)
async def recommend(
    request: Request,
    q: str | None = Query(
        default=None,
        description="Location query (e.g., 'Seattle, WA'). Enable via ENABLE_Q=true.",
    ),
    lat: float | None = Query(
        default=None,
        description="Latitude (-90 to 90). Required when not using q.",
        ge=-90,
        le=90,
    ),
    lon: float | None = Query(
        default=None,
        description="Longitude (-180 to 180). Required when not using q.",
        ge=-180,
        le=180,
    ),
    radius: int = Query(
        default=int(os.getenv("RECOMMEND_DEFAULT_RADIUS_MI", "100")),
        description="Search radius in miles (min 5).",
        ge=5,
    ),
    when: str | None = Query(
        default=None,
        description="Optional ISO datetime for forecast (e.g., '2024-12-30T12:00:00').",
    ),
    duration: int | None = Query(
        default=None,
        description="Desired sunshine duration in hours (1-12).",
        ge=1,
        le=12,
    ),
    get_weather_fn=Depends(get_weather_dep),
):
    # re-evaluate feature flag at request time to avoid stale import-time values
    enable_q = os.getenv("ENABLE_Q", "false").lower() == "true"

    # input validation
    if not enable_q and q is not None:
        return JSONResponse(
            status_code=400,
            content=ErrorPayload(
                error="geocoding_disabled",
                detail="Query (?q=) is disabled; provide lat/lon or set ENABLE_Q=true.",
                hint="Use ?lat=..&lon=..",
            ).model_dump(),
        )
    if enable_q:
        if (q is None) == (lat is None or lon is None):
            return JSONResponse(
                status_code=400,
                content=ErrorPayload(
                    error="invalid_params",
                    detail="Provide either q OR lat+lon, not both.",
                    hint="Example: /recommend?lat=47.6&lon=-122.3",
                ).model_dump(),
            )
    else:
        if lat is None or lon is None:
            # Tests expect a 422 for missing parameters
            return JSONResponse(
                status_code=422,
                content=ErrorPayload(
                    error="missing_coords",
                    detail="lat and lon are required.",
                    hint="Example: /recommend?lat=47.6&lon=-122.3",
                ).model_dump(),
            )

    # clamp radius
    rmin, rmax = 5, int(os.getenv("RECOMMEND_MAX_RADIUS_MI", "300"))
    radius = max(rmin, min(radius, rmax))

    # origin
    if lat is not None and lon is not None:
        origin = (lat, lon)
    else:
        # (Phase B) geocode path when enabled: resolve q -> lat/lon
        from Backend.models.errors import LocationNotFound as _LN
        from Backend.services.geocode import geocode as _geocode

        try:
            # q is validated by earlier logic to be present when we take the
            # geocode path; assert for the type-checker so mypy knows it's a str.
            assert q is not None
            origin = await _geocode(q)
        except _LN:
            return JSONResponse(
                status_code=422,
                content=ErrorPayload(
                    error="location_not_found",
                    detail=f"No location found for query: {q}",
                    hint="Try a more specific query (e.g., 'Seattle, WA')",
                ).model_dump(),
            )

    # candidates & ranking
    cand = nearby(origin[0], origin[1], radius, max_candidates=60)
    # Dev bypass: when set, return nearest candidates without calling weather
    if os.getenv("DEV_BYPASS_SCORING", "false").lower() == "true":
        top_n = int(os.getenv("RECOMMEND_TOP_N", "3"))
        results = []
        used_photo_ids: set[str] = set()
        for r in cand[:top_n]:
            # minimal shape expected by Recommendation
            r_out = {
                "id": str(r["id"]),
                "name": _clean_name(r["name"]),
                "lat": r["lat"],
                "lon": r["lon"],
                "elevation": r.get("elevation", 0.0),
                "category": r.get("category", ""),
                "state": r.get("state", ""),
                "timezone": r.get("timezone", "America/Los_Angeles"),
                "distance_mi": round(r["distance_mi"], 1),
                "sun_start_iso": None,
                "duration_hours": 0,
                "score": 0.0,
                "photo_id": _choose_photo_id_unique(
                    str(r["id"]), r.get("category", ""), used_photo_ids
                ),
            }
            results.append(Recommendation(**r_out))

        response_obj = RecommendResponse(
            query={"lat": origin[0], "lon": origin[1], "radius": radius},
            results=results,
            version="v1",
        )
        payload = response_obj.model_dump()
        payload_out = dict(payload)
        payload_out["recommendations"] = payload_out.get("results")
        payload_json = json.dumps(
            payload_out,
            default=str,
            separators=(",", ":"),
            sort_keys=True,
        )
        resp = JSONResponse(content=json.loads(payload_json))
        etag = strong_etag_for_obj(
            {k: v for k, v in payload.items() if k != "generated_at"}
        )
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = (
            "public, max-age=900, stale-while-revalidate=300"
        )
        resp.headers["X-Processing-Time"] = "TBD"
        resp.headers["Last-Modified"] = response_obj.generated_at.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )
        return resp
    # Allow tests to override the weather fetch dependency
    # get_weather_fn is expected to be a callable (lat, lon) -> (slots, status)
    weather_fetch = get_weather_fn or None
    if weather_fetch is None:
        # default to services.weather.get_weather_cached
        from Backend.services.weather import get_weather_cached as _default_get_weather

        weather_fetch = _default_get_weather

    try:
        ranked = await rank(
            origin[0],
            origin[1],
            cand,
            max_weather=int(os.getenv("WEATHER_FANOUT_MAX_CANDIDATES", "20")),
            weather_fetch=weather_fetch,
        )
    except WeatherError:
        return JSONResponse(
            status_code=502,
            content=ErrorPayload(
                error="weather_unavailable",
                detail="Weather service unavailable",
                hint="Try again later",
            ).model_dump(),
        )

    top_n = int(os.getenv("RECOMMEND_TOP_N", "3"))
    results = []
    # Track photo ids assigned so we avoid duplicates when auto-generating
    # Initialize only if not already set earlier in this function/path.
    try:
        used_photo_ids
    except NameError:
        used_photo_ids = set()
    for r in ranked[:top_n]:
        # Enforce float rounding policy
        r["distance_mi"] = round(r["distance_mi"], 1)
        r["score"] = round(r["score"], 2)
        if "name" in r:
            r["name"] = _clean_name(str(r["name"]))
        # Attach deterministic-but-unique-in-response photo id (optional)
        if "photo_id" not in r or not r["photo_id"]:
            pid = _choose_photo_id_unique(
                str(r.get("id", "")), r.get("category", ""), used_photo_ids
            )
            if pid:
                r["photo_id"] = pid
        results.append(Recommendation(**r))

    # Compose response
    response_obj = RecommendResponse(
        query={"lat": origin[0], "lon": origin[1], "radius": radius},
        results=results,
        version="v1",
    )
    # Full payload for the response
    payload = response_obj.model_dump()

    # Compute ETag over the payload excluding volatile fields (generated_at)
    etag_payload = {k: v for k, v in payload.items() if k != "generated_at"}
    # Use the helper that canonicalizes Python objects (stable floats, sorted keys)
    etag = strong_etag_for_obj(etag_payload)

    # If-None-Match support
    # Support If-None-Match with quoted or unquoted ETags, and comma-separated lists
    inm = request.headers.get("if-none-match")

    def _normalize_tag(tag: str) -> str:
        return tag.strip().strip('"')

    if inm:
        # header can contain multiple ETags separated by commas
        parts = [p.strip() for p in inm.split(",") if p.strip()]
        for p in parts:
            if _normalize_tag(p) == _normalize_tag(etag):
                # Return empty 304 to avoid mismatched Content-Length
                headers = {
                    "ETag": etag,
                    "Cache-Control": "public, max-age=900, stale-while-revalidate=300",
                    "X-Processing-Time": "TBD",
                    "Last-Modified": response_obj.generated_at.strftime(
                        "%a, %d %b %Y %H:%M:%S GMT"
                    ),
                }
                return Response(status_code=304, content=b"", headers=headers)

    # Include full payload (with generated_at); ensure JSON serializable
    # include a legacy 'recommendations' alias in the response payload for older tests
    payload_out = dict(payload)
    payload_out["recommendations"] = payload_out.get("results")
    payload_json = json.dumps(
        payload_out, default=str, separators=(",", ":"), sort_keys=True
    )
    resp = JSONResponse(content=json.loads(payload_json))
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "public, max-age=900, stale-while-revalidate=300"
    resp.headers["X-Processing-Time"] = "TBD"
    resp.headers["Last-Modified"] = response_obj.generated_at.strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    return resp
