import os
import json
from fastapi import APIRouter, Query, Request, Depends
from Backend.models.errors import UpstreamError as WeatherError
from fastapi.responses import JSONResponse, Response
from Backend.models.recommendation import RecommendResponse, Recommendation
from Backend.models.errors import ErrorPayload
from Backend.services.locations import nearby
from Backend.services.scoring import rank
from Backend.utils.etag import strong_etag_for_obj

router = APIRouter()
ENABLE_Q = os.getenv("ENABLE_Q","false").lower() == "true"


def get_weather_dep():
    """Dependency provider for weather fetch function; tests override this."""
    return None

@router.get(
    "/recommend",
    response_model=RecommendResponse,
    summary="Get sunshine location recommendations",
    tags=["recommendations"],
    description="""
Get personalized sunshine location recommendations based on geographic coordinates and weather forecasts.

This endpoint finds nearby locations within the Pacific Northwest region, analyzes weather forecasts
to identify optimal sunshine windows, and returns ranked recommendations with comprehensive location
metadata including category, elevation, and local timezone information.

**Key Features:**
- Weather-based scoring using cloud cover and sunshine duration
- Rich location metadata (category, elevation, state, timezone)
- Conditional request support (ETag/If-None-Match for 304 responses)
- Distance-based filtering with configurable radius
- Deterministic results for consistent caching

**Scoring Algorithm:**
Locations are scored based on earliest sunny weather windows (≤30% cloud cover) between 08:00-18:00 local time,
weighted by sunshine duration and distance from origin. Scores range from 0-100 (higher is better).

**Location Categories:**
Forest, Gorge, Beach, Lake, Mountain, Valley, and other natural recreation areas.

**Geographic Coverage:**
Pacific Northwest region including Washington, Oregon, and Idaho.
    """,
    responses={
        200: {
            "description": "Successful recommendation response with ranked locations",
            "content": {
                "application/json": {
                    "example": {
                        "query": {"lat": 47.603243, "lon": -122.330286, "radius": 100},
                        "results": [
                            {
                                "id": "69",
                                "name": "Deception Pass_69",
                                "lat": 48.44522,
                                "lon": -122.615167,
                                "elevation": 0.0,
                                "category": "Forest",
                                "state": "WA",
                                "timezone": "America/Los_Angeles",
                                "distance_mi": 59.6,
                                "sun_start_iso": "2024-12-30T10:00",
                                "duration_hours": 6,
                                "score": 94.03
                            }
                        ],
                        "generated_at": "2024-12-30T18:00:00Z",
                        "version": "v1"
                    }
                }
            }
        },
        304: {"description": "Not Modified - content unchanged since last request (ETag match)"},
        400: {"description": "Bad Request - invalid parameters or geocoding disabled"},
        422: {"description": "Unprocessable Entity - missing required coordinates"},
        502: {"description": "Bad Gateway - weather service unavailable"},
        504: {"description": "Gateway Timeout - request exceeded time budget"}
    }
)
async def recommend(
    request: Request,
    q: str | None = Query(
        default=None, 
        description="Location query string (e.g., 'Seattle, WA'). Requires ENABLE_Q=true environment variable. Mutually exclusive with lat/lon."
    ),
    lat: float | None = Query(
        default=None, 
        description="Latitude in decimal degrees (-90 to 90). Required when not using q parameter.",
        ge=-90, 
        le=90
    ),
    lon: float | None = Query(
        default=None, 
        description="Longitude in decimal degrees (-180 to 180). Required when not using q parameter.",
        ge=-180, 
        le=180
    ),
    radius: int = Query(
        default=int(os.getenv("RECOMMEND_DEFAULT_RADIUS_MI","100")),
        description="Search radius in miles (5-300). Larger radius includes more distant locations but may impact performance.",
        ge=5,
        le=300
    ),
    when: str | None = Query(
        default=None,
        description="Future date/time for forecast in ISO format (e.g., '2024-12-30T12:00:00'). Defaults to near-future optimal time window."
    ),
    duration: int | None = Query(
        default=None,
        description="Desired sunshine duration in hours (1-12). Used for scoring preference.",
        ge=1,
        le=12
    ),
    get_weather_fn = Depends(get_weather_dep),
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
                hint="Use ?lat=..&lon=.."
            ).model_dump(),
        )
    if enable_q:
        if (q is None) == (lat is None or lon is None):
            return JSONResponse(
                status_code=400,
                content=ErrorPayload(
                    error="invalid_params",
                    detail="Provide either q OR lat+lon, not both.",
                    hint="Example: /recommend?lat=47.6&lon=-122.3"
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
                    hint="Example: /recommend?lat=47.6&lon=-122.3"
                ).model_dump(),
            )

    # clamp radius
    rmin, rmax = 5, int(os.getenv("RECOMMEND_MAX_RADIUS_MI","300"))
    radius = max(rmin, min(radius, rmax))

    # origin
    if lat is not None and lon is not None:
        origin = (lat, lon)
    else:
        # (Phase B) geocode path when enabled: resolve q -> lat/lon
        from Backend.services.geocode import geocode as _geocode
        from Backend.models.errors import LocationNotFound as _LN
        try:
            origin = await _geocode(q)
        except _LN:
            return JSONResponse(
                status_code=422,
                content=ErrorPayload(
                    error="location_not_found",
                    detail=f"No location found for query: {q}",
                    hint="Try a more specific query (e.g., 'Seattle, WA')"
                ).model_dump(),
            )

    # candidates & ranking
    cand = nearby(origin[0], origin[1], radius, max_candidates=60)
    # Dev bypass: when set, return nearest candidates without calling weather
    if os.getenv("DEV_BYPASS_SCORING", "false").lower() == "true":
        top_n = int(os.getenv("RECOMMEND_TOP_N","3"))
        results = []
        for r in cand[:top_n]:
            # minimal shape expected by Recommendation
            r_out = {
                "id": str(r["id"]),
                "name": r["name"],
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
            }
            results.append(Recommendation(**r_out))

        response_obj = RecommendResponse(
            query={"lat": origin[0], "lon": origin[1], "radius": radius},
            results=results,
        )
        payload = response_obj.model_dump()
        payload_out = dict(payload)
        payload_out["recommendations"] = payload_out.get("results")
        resp = JSONResponse(content=json.loads(json.dumps(payload_out, default=str, separators=(",",":"), sort_keys=True)))
        etag = strong_etag_for_obj({k: v for k, v in payload.items() if k != "generated_at"})
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "public, max-age=900, stale-while-revalidate=300"
        resp.headers["X-Processing-Time"] = "TBD"
        resp.headers["Last-Modified"] = response_obj.generated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
        return resp
    # Allow tests to override the weather fetch dependency
    # get_weather_fn is expected to be a callable (lat, lon) -> (slots, status)
    weather_fetch = get_weather_fn or None
    if weather_fetch is None:
        # default to services.weather.get_weather_cached
        from Backend.services.weather import get_weather_cached as _default_get_weather
        weather_fetch = _default_get_weather

    try:
        ranked = await rank(origin[0], origin[1], cand,
                            max_weather=int(os.getenv("WEATHER_FANOUT_MAX_CANDIDATES","20")),
                            weather_fetch=weather_fetch)
    except WeatherError:
        return JSONResponse(status_code=502, content=ErrorPayload(
            error="weather_unavailable",
            detail="Weather service unavailable",
            hint="Try again later"
        ).model_dump())

    top_n = int(os.getenv("RECOMMEND_TOP_N","3"))
    results = []
    for r in ranked[:top_n]:
        # Enforce float rounding policy
        r["distance_mi"] = round(r["distance_mi"], 1)
        r["score"] = round(r["score"], 2)
        results.append(Recommendation(**r))

    # Compose response
    response_obj = RecommendResponse(
        query={"lat": origin[0], "lon": origin[1], "radius": radius},
        results=results
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
                # Return an empty 304 Response (no body) to avoid mismatched Content-Length
                headers = {
                    "ETag": etag,
                    "Cache-Control": "public, max-age=900, stale-while-revalidate=300",
                    "X-Processing-Time": "TBD",
                    "Last-Modified": response_obj.generated_at.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                }
                return Response(status_code=304, content=b"", headers=headers)

    # Response should include the full payload (with generated_at); ensure JSON serializable
    # include a legacy 'recommendations' alias in the response payload for older tests
    payload_out = dict(payload)
    payload_out["recommendations"] = payload_out.get("results")
    resp = JSONResponse(content=json.loads(json.dumps(payload_out, default=str, separators=(",", ":"), sort_keys=True)))
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "public, max-age=900, stale-while-revalidate=300"
    resp.headers["X-Processing-Time"] = "TBD"
    resp.headers["Last-Modified"] = response_obj.generated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return resp
