import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from Backend.services.telemetry_sink import (
    enqueue_event,
    sink_event_forward_http,
    sink_event_jsonl,
)

router = APIRouter()
logger = logging.getLogger("sunshine_backend.telemetry")


class TelemetryEvent(BaseModel):
    event: str
    properties: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    source: Optional[str] = None


# In-memory recent events buffer (lightweight; useful for debugging during dev)
_RECENT_EVENTS: List[Dict[str, Any]] = []
_MAX_EVENTS = 200


@router.post("/telemetry", status_code=202)
async def ingest(event: TelemetryEvent):
    payload = event.model_dump()
    # Log structured-ish message for downstream log processors
    logger.info("ingest", extra={"telemetry": payload})

    # Keep a small in-memory buffer for quick inspection in dev
    try:
        _RECENT_EVENTS.append(payload)
        if len(_RECENT_EVENTS) > _MAX_EVENTS:
            _RECENT_EVENTS.pop(0)
    except Exception:
        logger.exception("Failed to append telemetry to buffer")

    # Enqueue for batching if available; otherwise fallback to immediate sink
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(enqueue_event(payload))
    except RuntimeError:
        # Fallback: write immediately
        try:
            asyncio.ensure_future(sink_event_jsonl(payload))
            asyncio.ensure_future(sink_event_forward_http(payload))
        except Exception:
            logger.exception("Failed to schedule telemetry sinks")

    return {"status": "accepted"}


@router.get("/telemetry/recent")
async def recent():
    # Expose recent events for quick debugging (do not enable in production)
    return {"count": len(_RECENT_EVENTS), "events": _RECENT_EVENTS}
