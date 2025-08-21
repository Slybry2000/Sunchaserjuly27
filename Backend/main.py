from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request
from Backend.services.geocode import geocode
from Backend.utils.cache import cached
from Backend.services.http import get_http_client, close_http_client
from Backend.middleware.observability import ObservabilityMiddleware
from Backend.routers.recommend import router as recommend_router
from Backend.routers.internal import router as internal_router
from Backend.routers.forecasts import router as forecasts_router
from Backend.models.errors import ErrorPayload, UpstreamError, LocationNotFound, SchemaError, TimeoutBudgetExceeded
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
app.add_middleware(ObservabilityMiddleware)

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
    