import os, json
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from models.recommendation import RecommendResponse, Recommendation
from models.errors import ErrorPayload
from services.locations import nearby
from services.scoring import rank
from utils.etag import strong_etag

router = APIRouter()
ENABLE_Q = os.getenv("ENABLE_Q","false").lower() == "true"

@router.get("/recommend")
async def recommend(
    request: Request,
    q: str | None = Query(default=None),
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    radius: int = Query(default=int(os.getenv("RECOMMEND_DEFAULT_RADIUS_MI","100")))
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
            return JSONResponse(
                status_code=400,
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
    ranked = await rank(origin[0], origin[1], cand,
                        max_weather=int(os.getenv("WEATHER_FANOUT_MAX_CANDIDATES","20")))

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
    payload = response_obj.model_dump(mode="json")

    # stable bytes for ETag (sorted keys, minified)
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    etag = strong_etag(body)

    # If-None-Match support
    inm = request.headers.get("if-none-match")
    if inm and inm == etag:
        return JSONResponse(status_code=304, content=None, headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=900, stale-while-revalidate=300",
            "X-Processing-Time": "TBD",
            "Last-Modified": response_obj.generated_at.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        })

    resp = JSONResponse(content=json.loads(body))
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "public, max-age=900, stale-while-revalidate=300"
    resp.headers["X-Processing-Time"] = "TBD"
    resp.headers["Last-Modified"] = response_obj.generated_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return resp
