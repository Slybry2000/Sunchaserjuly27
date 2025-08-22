from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request
from Backend.services.geocode import geocode
from Backend.utils.cache import cached
from Backend.services.http import get_http_client, close_http_client
from Backend.middleware.observability import ObservabilityMiddleware
from typing import cast, Any as _Any
from Backend.routers.recommend import router as recommend_router
from Backend.routers.internal import router as internal_router
from Backend.routers.forecasts import router as forecasts_router
from Backend.models.errors import ErrorPayload, UpstreamError, LocationNotFound, SchemaError, TimeoutBudgetExceeded

import os
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize shared resources (e.g., HTTP client)
    await get_http_client()
    try:
        yield
    finally:
        # Cleanup shared resources
        await close_http_client()

app = FastAPI(title="Sunshine Backend API", version="1.0.0", lifespan=lifespan)
app.include_router(recommend_router)
app.include_router(internal_router)
app.include_router(forecasts_router)

# Add observability middleware
app.add_middleware(cast(_Any, ObservabilityMiddleware))

# CORS configuration
logger = logging.getLogger('sunshine_backend')
dev_allow = os.environ.get('DEV_ALLOW_CORS', '').lower() in ('1', 'true', 'yes')
cors_allowed = os.environ.get('CORS_ALLOWED_ORIGINS', '').strip()

if dev_allow:
    # Permissive CORS for local development/debugging
    app.add_middleware(
        cast(_Any, CORSMiddleware),
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info('DEV_ALLOW_CORS enabled: permissive CORS (allow_origins=*)')
elif cors_allowed:
    # Normalize origins (strip whitespace and trailing slash) for comparison
    origins = [o.strip().rstrip('/') for o in cors_allowed.split(',') if o.strip()]
    app.add_middleware(
        cast(_Any, CORSMiddleware),
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    logger.info('CORS allowlist configured: %s', origins)

    # Add lightweight logging middleware to record rejected origins. This does
    # not change browser CORS behavior (CORSMiddleware still controls headers),
    # but it surfaces attempts from disallowed origins in the server logs for
    # auditing and incident response.
    # Optional enforcement: when true, respond with 403 for disallowed origins
    cors_enforce = os.environ.get('CORS_ENFORCE', '').lower() in ('1', 'true', 'yes')

    @app.middleware("http")
    async def cors_rejected_logging_middleware(request: Request, call_next):
        origin = request.headers.get('origin')
        if origin:
            norm = origin.rstrip('/')
            if norm not in origins:
                client = request.client.host if request.client else 'unknown'
                # Structured-ish log fields for easier parsing in log sinks
                logger.warning(
                    'Rejected CORS origin', extra={
                        'origin': origin,
                        'path': request.url.path,
                        'method': request.method,
                        'client': client,
                    }
                )
                if cors_enforce:
                    # Return a JSON error payload for disallowed origins when enforcement enabled
                    return JSONResponse(
                        status_code=403,
                        content={
                            'error': 'cors_forbidden',
                            'detail': f'Origin {origin} not allowed',
                        },
                    )
        return await call_next(request)

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
        content=ErrorPayload(error="timeout_budget_exceeded", detail=str(exc)).model_dump(),
    )

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.get('/geocode')
@cached(ttl=604800, key_prefix="geocode")  # 7 days TTL
async def geocode_endpoint(q: str = Query(..., description="Location query (e.g., 'Seattle, WA')")):
    """
    Geocode a location query to latitude/longitude coordinates
    """
    try:
        lat, lon = await geocode(q)
        return {
            "query": q,
            "lat": lat,
            "lon": lon
        }
    except LocationNotFound:
        raise
    except ValueError as e:
        raise SchemaError(str(e)) from e
    