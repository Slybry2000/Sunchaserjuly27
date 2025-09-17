from typing import Any, Dict, Optional

from pydantic import BaseModel


class PhotoMetaResponse(BaseModel):
    """Response model for photo metadata endpoint."""

    id: str
    urls: Dict[str, str]
    links: Dict[str, str]
    attribution_html: str
    source: str  # 'live', 'demo', or 'random'
    random_fallback: Optional[bool] = None
    debug: Optional[Dict[str, Any]] = None


class TrackResponse(BaseModel):
    """Response model for photo tracking endpoint."""

    tracked: bool
    reason: Optional[str] = None  # 'deduped', 'missing_params', 'api_failure', 'mocked'


class TrackRequest(BaseModel):
    """Request model for photo tracking."""

    download_location: Optional[str] = None
    photo_id: Optional[str] = None
