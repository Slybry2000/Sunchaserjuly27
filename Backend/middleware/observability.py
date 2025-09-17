import json
import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Use a dedicated logger to avoid uvicorn access log formatting conflicts
app_logger = logging.getLogger("sun.observ")
if not app_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.time()
        response = await call_next(request)
        duration = int((time.time() - start) * 1000)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time"] = str(duration)
        # Keep the logged payload compact to avoid long-line lints
        payload = {
            "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "id": request_id,
            "m": request.method,
            "p": request.url.path,
            "s": response.status_code,
            "lat": duration,
        }
        app_logger.info(json.dumps(payload))
        return response
