import os, json
from fastapi import APIRouter, Query, Request, Depends
from models.errors import UpstreamError as WeatherError
from fastapi.responses import JSONResponse
from models.recommendation import RecommendResponse, Recommendation
from models.errors import ErrorPayload
from services.locations import nearby
from services.scoring import rank
from utils.etag import strong_etag

router = APIRouter()
ENABLE_Q = os.getenv("ENABLE_Q","false").lower() == "true"


def get_weather_dep():
    """Dependency provider for weather fetch function; tests override this."""
    return None

@router.get("/recommend")
async def recommend(
    request: Request,
    q: str | None = Query(default=None),
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    radius: int = Query(default=int(os.getenv("RECOMMEND_DEFAULT_RADIUS_MI","100"))),
    get_weather_fn = Depends(get_weather_dep),
):
    # input validation
    if not ENABLE_Q and q is not None:
        return JSONResponse(
            status_code=400,
            content=ErrorPayload(
                error="geocoding_disabled",
                detail="Query (?q=) is disabled; provide lat/lon or set ENABLE_Q=true.",
                hint="Use ?lat=..&lon=.."
            ).model_dump(),
        )
    if ENABLE_Q:
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
        # (Phase B) geocode path when enabled; for Phase A, not used.
        return JSONResponse(
            status_code=501,
            content=ErrorPayload(
                error="not_implemented",
                detail="Geocode path deferred in Phase A.",
                hint="Use lat/lon"
            ).model_dump(),
        )

    # candidates & ranking
    cand = nearby(origin[0], origin[1], radius, max_candidates=60)
    # Allow tests to override the weather fetch dependency
    # get_weather_fn is expected to be a callable (lat, lon) -> (slots, status)
    weather_fetch = get_weather_fn or None
    if weather_fetch is None:
        # default to services.weather.get_weather_cached
        from services.weather import get_weather_cached as _default_get_weather
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
    # ensure datetimes are serialized consistently
    body = json.dumps(etag_payload, default=str, separators=(",", ":"), sort_keys=True).encode("utf-8")
    etag = strong_etag(body)

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
                return JSONResponse(status_code=304, content=None, headers={
                    "ETag": etag,
                    "Cache-Control": "public, max-age=900, stale-while-revalidate=300",
                    "X-Processing-Time": "TBD",
                    "Last-Modified": response_obj.generated_at.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                })

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
