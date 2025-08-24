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

app = FastAPI(
    title="Sunshine Backend API",
    version="1.0.0",
    description="""
# Sunshine Location Recommendation API

A FastAPI service for finding optimal sunshine locations in the Pacific Northwest based on weather forecasts and geographic data.

## Key Features

- **Weather-Based Recommendations**: Analyzes cloud cover and sunshine patterns to identify optimal outdoor locations
- **Rich Location Metadata**: 100+ curated locations with categories (Forest, Gorge, Beach, Lake), elevation, and timezone data
- **Intelligent Scoring**: Combines weather quality, sunshine duration, and distance for personalized recommendations
- **Conditional Requests**: ETag/If-None-Match support for efficient caching and bandwidth optimization
- **Geographic Coverage**: Washington, Oregon, and Idaho with comprehensive Pacific Northwest coverage

## API Highlights

- **GET /recommend**: Primary endpoint for sunshine location recommendations
- **GET /health**: Service health and readiness checks
- **GET /geocode**: Location name to coordinates conversion (when enabled)
- **GET /forecasts**: Weather forecast data access

## Dataset

Our curated dataset includes 100 unique Pacific Northwest locations with:
- Geographic coordinates and elevation data
- Location categories for activity matching
- State and timezone information for local time calculations
- Distance-based filtering for personalized radius preferences

## Scoring Algorithm

Locations are ranked using a sophisticated algorithm that considers:
1. **Weather Quality**: Cloud cover ≤30% during daylight hours (08:00-18:00 local time)
2. **Sunshine Duration**: Continuous sunny periods weighted by requested duration
3. **Distance Factor**: Proximity to origin with configurable radius preferences
4. **Time Optimization**: Earliest available sunshine windows for immediate planning

Scores range from 0-100 with higher values indicating better sunshine opportunities.

## Performance & Caching

- In-process SWR (Stale-While-Revalidate) cache with TTL and LRU eviction
- Weather API integration with retry logic and timeout budgets
- Deterministic JSON responses for reliable ETag generation
- Background refresh capabilities for high-availability scenarios

## Error Handling

Comprehensive error taxonomy with specific HTTP status codes:
- 400: Invalid parameters or disabled features
- 422: Missing required coordinates
- 502: Upstream weather service unavailable
- 504: Request timeout exceeded

Perfect for mobile apps, web services, and outdoor recreation platforms requiring reliable sunshine forecasting.
    """,
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
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.sunshine.example.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "recommendations",
            "description": "Core sunshine location recommendation functionality"
        },
        {
            "name": "health",
            "description": "Service health monitoring and diagnostics"
        },
        {
            "name": "geocoding",
            "description": "Location name to coordinate conversion services"
        },
        {
            "name": "forecasts",
            "description": "Weather forecast data access and caching"
        }
    ]
)
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

# Optional beta key gate: when BETA_KEYS is set (comma-separated), require X-Beta-Key
# header on incoming requests. Exempt health and debug endpoints and OPTIONS preflight
# so monitoring and CORS preflight continue to function. This is intentionally
# lightweight and intended for small tester allowlists during Phase C beta.
beta_keys_env = os.environ.get('BETA_KEYS', '').strip()
if beta_keys_env:
    _beta_keys = {k.strip() for k in beta_keys_env.split(',') if k.strip()}
    logger.info('BETA_KEYS configured: %d keys', len(_beta_keys))

    @app.middleware("http")
    async def beta_key_middleware(request: Request, call_next):
        # Allow CORS preflight and public health/debug endpoints without a key
        if request.method == 'OPTIONS':
            return await call_next(request)

        # Exempt simple health/debug endpoints so uptime checks continue to work
        if request.url.path in ('/health', '/_debug_env'):
            return await call_next(request)

        header = request.headers.get('x-beta-key') or request.headers.get('X-Beta-Key')
        if not header:
            return JSONResponse(
                status_code=401,
                content={
                    'error': 'beta_key_required',
                    'detail': 'Missing X-Beta-Key header',
                },
            )
        if header not in _beta_keys:
            return JSONResponse(
                status_code=401,
                content={
                    'error': 'beta_key_invalid',
                    'detail': 'Invalid X-Beta-Key',
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

@app.get(
    '/health',
    tags=["health"],
    summary="Service health check",
    description="Returns service health status for monitoring and load balancer health checks.",
    responses={
        200: {
            "description": "Service is healthy and ready to accept requests",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
async def health():
    """Service health check endpoint for monitoring and load balancers."""
    return {'status': 'ok'}


@app.get('/_debug_env')
async def _debug_env():
    """Temporary debug endpoint: reports whether MAPBOX_TOKEN is visible in the process.

    This endpoint is intended only for local debugging during restart troubleshooting
    and can be removed once we've confirmed environment propagation.
    """
    token = os.getenv('MAPBOX_TOKEN')
    return {
        'has_mapbox': bool(token),
        'mapbox_len': len(token) if token else 0,
    }

@app.get(
    '/geocode',
    tags=["geocoding"],
    summary="Convert location name to coordinates",
    description="""
Convert a human-readable location query to latitude/longitude coordinates using Mapbox Geocoding API.

Supports various location formats including:
- City and state (e.g., "Seattle, WA")
- Full addresses
- Landmarks and points of interest
- Natural features and parks

Results are cached for 7 days to optimize performance and reduce API calls.

**Note**: This endpoint requires a valid MAPBOX_TOKEN environment variable and may be disabled
in some deployment configurations.
    """,
    responses={
        200: {
            "description": "Successful geocoding response with coordinates",
            "content": {
                "application/json": {
                    "example": {
                        "query": "Seattle, WA",
                        "lat": 47.603243,
                        "lon": -122.330286,
                        "address": "Seattle, Washington, United States"
                    }
                }
            }
        },
        400: {"description": "Bad Request - invalid query parameter"},
        401: {"description": "Unauthorized - invalid or missing Mapbox token"},
        502: {"description": "Bad Gateway - geocoding service unavailable"},
        504: {"description": "Gateway Timeout - geocoding request timeout"}
    }
)
@cached(ttl=604800, key_prefix="geocode")  # 7 days TTL
async def geocode_endpoint(q: str = Query(..., description="Location query (e.g., 'Seattle, WA')")):
    """
    Geocode a location query to latitude/longitude coordinates using Mapbox API.
    
    Converts human-readable location names to precise geographic coordinates
    for use with the recommendation engine.
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
    