import logging
import os
from contextlib import asynccontextmanager
from typing import Any as _Any
from typing import cast

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from Backend.middleware.observability import ObservabilityMiddleware
from Backend.models.errors import (
    ErrorPayload,
    LocationNotFound,
    SchemaError,
    TimeoutBudgetExceeded,
    UpstreamError,
)
from Backend.routers.forecasts import router as forecasts_router
from Backend.routers.internal import router as internal_router
from Backend.routers.recommend import router as recommend_router
from Backend.routers.telemetry import router as telemetry_router
from Backend.routers.unsplash import router as unsplash_router
from Backend.services.geocode import geocode
from Backend.services.http import close_http_client, get_http_client
from Backend.services.metrics import get_metrics, prometheus_metrics
from Backend.services.telemetry_sink import (
    start_telemetry_batcher,
    stop_telemetry_batcher,
)
from Backend.utils.cache import cached
from datetime import datetime
import subprocess


def _compute_build_info():
    sha = os.environ.get("GIT_COMMIT_SHA")
    if not sha:
        try:
            sha = (
                subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])  # nosec B603
                .decode("utf-8")
                .strip()
            )
        except Exception:
            sha = "unknown"
    ts = os.environ.get("BUILD_TIMESTAMP") or datetime.utcnow().isoformat() + "Z"
    tag = os.environ.get("GIT_TAG", "")
    return {"commit": sha, "timestamp": ts, "tag": tag}

_BUILD_INFO = _compute_build_info()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize shared resources (e.g., HTTP client)
    await get_http_client()
    # start telemetry batcher if configured
    try:
        await start_telemetry_batcher()
    except Exception:
        logging.getLogger("sunshine_backend.telemetry.sink").exception(
            "Failed to start telemetry batcher"
        )
    try:
        yield
    finally:
        # Cleanup shared resources
        await close_http_client()
        try:
            await stop_telemetry_batcher()
        except Exception:
            logging.getLogger("sunshine_backend.telemetry.sink").exception(
                "Failed to stop telemetry batcher"
            )


app = FastAPI(
    title="Sunshine Backend API",
    version="1.0.0",
    description=(
        "Sunshine Location Recommendation API. A FastAPI service for finding "
        "optimal sunshine locations in the Pacific Northwest based on weather "
        "forecasts and geographic data."
        "\n\nKey features include weather-based recommendations, rich location "
        "metadata, and an intelligent scoring engine. The service supports "
        "ETag/If-None-Match for efficient caching and provides geocoding, "
        "forecast access, and a primary /recommend endpoint."
    ),
    lifespan=lifespan,
    contact={
        "name": "Sunshine API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.sunshine.example.com", "description": "Production server"},
    ],
    tags_metadata=[
        {
            "name": "recommendations",
            "description": "Core sunshine location recommendation functionality",
        },
        {"name": "health", "description": "Service health monitoring and diagnostics"},
        {
            "name": "geocoding",
            "description": "Location name to coordinate conversion services",
        },
        {
            "name": "forecasts",
            "description": "Weather forecast data access and caching",
        },
    ],
)
app.include_router(recommend_router)
app.include_router(internal_router)
app.include_router(forecasts_router)
app.include_router(telemetry_router)
app.include_router(unsplash_router)

# Add observability middleware
cast(_Any, app).add_middleware(cast(_Any, ObservabilityMiddleware))

# CORS configuration
logger = logging.getLogger("sunshine_backend")
dev_allow = os.environ.get("DEV_ALLOW_CORS", "").lower() in ("1", "true", "yes")
cors_allowed = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()

if dev_allow:
    # Permissive CORS for local development/debugging
    cast(_Any, app).add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Length"],
        max_age=600,
    )
    logger.info("DEV_ALLOW_CORS enabled: permissive CORS (allow_origins=*)")
elif cors_allowed:
    # Normalize origins (strip whitespace and trailing slash) for comparison
    origins = [o.strip().rstrip("/") for o in cors_allowed.split(",") if o.strip()]
    cast(_Any, app).add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Length"],
        max_age=600,
    )
    logger.info("CORS allowlist configured: %s", origins)

    # Log rejected CORS origins for auditing.
    # Optionally enforce by returning 403 when CORS_ENFORCE is enabled.
    cors_enforce = os.environ.get("CORS_ENFORCE", "").lower() in ("1", "true", "yes")

    @app.middleware("http")
    async def cors_rejected_logging_middleware(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin:
            norm = origin.rstrip("/")
            if norm not in origins:
                client = request.client.host if request.client else "unknown"
                # Structured-ish log fields for easier parsing in log sinks
                extra = {
                    "origin": origin,
                    "path": request.url.path,
                    "method": request.method,
                    "client": client,
                }
                logger.warning("Rejected CORS origin", extra=extra)
                if cors_enforce:
                    # Return JSON error when enforcement enabled
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": "cors_forbidden",
                            "detail": f"Origin {origin} not allowed",
                        },
                    )
        return await call_next(request)


# Beta key gate middleware: always register a middleware that checks the
# BETA_KEYS environment variable at request time. This avoids import-order
# test flakiness where tests set env vars after the app has been constructed.
class BetaKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *args, **kwargs):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Allow CORS preflight and public health/debug endpoints without a key
        if request.method == "OPTIONS":
            return await call_next(request)

        # Exempt simple health/debug endpoints and telemetry ingestion so uptime
        # checks and client-side telemetry can work without a beta key.
        if request.url.path in ("/health", "/_debug_env", "/telemetry"):
            return await call_next(request)

        # Read keys at request time so tests that mutate env before a request
        # are honored even if the app was constructed earlier.
        env = os.environ.get("BETA_KEYS", "").strip()
        if not env:
            # No keys configured -> no gating enforced
            return await call_next(request)

        keys = {k.strip() for k in env.split(",") if k.strip()}
        header = request.headers.get("x-beta-key") or request.headers.get("X-Beta-Key")
        if not header:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "beta_key_required",
                    "detail": "Missing X-Beta-Key header",
                },
            )
        if header not in keys:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "beta_key_invalid",
                    "detail": "Invalid X-Beta-Key",
                },
            )
        return await call_next(request)


# Always register the middleware so it runs before FastAPI validation. The
# middleware is a no-op unless BETA_KEYS is set in the environment at request
# time.
cast(_Any, app).add_middleware(BetaKeyMiddleware)


# Exception handlers for error taxonomy
@app.exception_handler(UpstreamError)
async def upstream_error_handler(request: Request, exc: UpstreamError):
    return JSONResponse(
        status_code=502,
        content=ErrorPayload(error="upstream_error", detail=str(exc)).model_dump(),
    )


@app.exception_handler(LocationNotFound)
async def location_not_found_handler(request: Request, exc: LocationNotFound):
    return JSONResponse(
        status_code=404,
        content=ErrorPayload(error="location_not_found", detail=str(exc)).model_dump(),
    )


@app.exception_handler(SchemaError)
async def schema_error_handler(request: Request, exc: SchemaError):
    return JSONResponse(
        status_code=422,
        content=ErrorPayload(error="schema_error", detail=str(exc)).model_dump(),
    )


@app.exception_handler(TimeoutBudgetExceeded)
async def timeout_budget_handler(request: Request, exc: TimeoutBudgetExceeded):
    return JSONResponse(
        status_code=504,
        content=ErrorPayload(
            error="timeout_budget_exceeded", detail=str(exc)
        ).model_dump(),
    )


@app.get(
    "/health",
    tags=["health"],
    summary="Service health check",
    description="Service health status for monitoring and load balancers.",
    responses={
        200: {
            "description": "Service is healthy and ready to accept requests",
            "content": {"application/json": {"example": {"status": "ok"}}},
        }
    },
)
async def health():
    """Service health check endpoint for monitoring and load balancers."""
    return {"status": "ok"}


@app.get("/_debug_env")
async def _debug_env():
    """Temporary debug endpoint: reports whether MAPBOX_TOKEN is visible in the process.

    This endpoint is intended only for local debugging during restart troubleshooting
    and can be removed once we've confirmed environment propagation.
    """
    token = os.getenv("MAPBOX_TOKEN")
    unsplash = os.getenv("UNSPLASH_CLIENT_ID")
    # Do not return the actual key; only return presence and length for local debugging
    return {
        "has_mapbox": bool(token),
        "mapbox_len": len(token) if token else 0,
        "has_unsplash_key": bool(unsplash),
        "unsplash_key_len": len(unsplash) if unsplash else 0,
    }


@app.get("/metrics")
async def metrics_endpoint():
    """Expose metrics: Prometheus text when available, otherwise JSON counters."""
    try:
        data = prometheus_metrics()
        # prometheus_metrics returns bytes
        media_type = "text/plain; version=0.0.4; charset=utf-8"
        decoded = data.decode("utf-8")
        return JSONResponse(content=decoded, media_type=media_type)
    except Exception:
        # fallback to JSON counters
        return get_metrics()


@app.get("/internal/version", tags=["health"], summary="Build/version info")
async def version_info():
    """Return build metadata (commit SHA, build timestamp, optional tag)."""
    return _BUILD_INFO


@app.get(
    "/geocode",
    tags=["geocoding"],
    summary="Convert location name to coordinates",
    description=(
        "Convert a location query to latitude/longitude using Mapbox. "
        "Supports city/state, addresses, landmarks, and natural features. "
        "Results are cached for 7 days. Requires MAPBOX_TOKEN when enabled."
    ),
    responses={
        200: {
            "description": "Successful geocoding response with coordinates",
            "content": {
                "application/json": {
                    "example": {
                        "query": "Seattle, WA",
                        "lat": 47.603243,
                        "lon": -122.330286,
                        "address": "Seattle, Washington, United States",
                    }
                }
            },
        },
        400: {"description": "Bad Request - invalid query parameter"},
        401: {"description": "Unauthorized - invalid or missing Mapbox token"},
        502: {"description": "Bad Gateway - geocoding service unavailable"},
        504: {"description": "Gateway Timeout - geocoding request timeout"},
    },
)
@cached(ttl=604800, key_prefix="geocode")  # 7 days TTL
async def geocode_endpoint(
    q: str = Query(..., description="Location query (e.g., 'Seattle, WA')")
):
    """
    Geocode a location query to latitude/longitude coordinates using Mapbox API.

    Converts human-readable location names to precise geographic coordinates
    for use with the recommendation engine.
    """
    try:
        lat, lon = await geocode(q)
        return {"query": q, "lat": lat, "lon": lon}
    except LocationNotFound:
        raise
    except ValueError as e:
        raise SchemaError(str(e)) from e
