from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """A recommended sunshine location with weather forecast and metadata."""

    id: str = Field(..., description="Location id")
    name: str = Field(..., description="Human-readable name")
    lat: float = Field(..., description="Latitude", ge=-90, le=90)
    lon: float = Field(..., description="Longitude", ge=-180, le=180)
    elevation: float = Field(..., description="Elevation in feet")
    category: str = Field(..., description="Category (e.g., Forest, Beach)")
    state: str = Field(..., description="State abbreviation (WA, OR, ID)")
    timezone: str = Field(..., description="IANA timezone id")
    distance_mi: float = Field(..., description="Distance from origin in miles")
    sun_start_iso: Optional[str] = Field(
        None, description="ISO 8601 local time when sunshine begins"
    )
    duration_hours: int = Field(
        0, description="Expected sunshine duration (hours)", ge=0
    )
    score: float = Field(..., description="Recommendation score (0-100)")
    photo_id: Optional[str] = Field(
        None, description="Unsplash photo id for attribution/tracking (optional)"
    )


class Location(BaseModel):
    """A location in the dataset with geographic and descriptive metadata."""

    id: int = Field(..., description="Unique numeric identifier for the location")
    name: str = Field(..., description="Human-readable location name")
    lat: float = Field(..., description="Latitude in decimal degrees", ge=-90, le=90)
    lon: float = Field(..., description="Longitude in decimal degrees", ge=-180, le=180)
    elevation: float = Field(..., description="Elevation above sea level in feet")
    category: str = Field(
        ..., description="Location category (e.g., Forest, Gorge, Beach, Lake)"
    )
    state: str = Field(..., description="US state abbreviation (WA, OR, ID)")
    timezone: str = Field(
        ..., description="IANA timezone identifier (e.g., America/Los_Angeles)"
    )


class RecommendResponse(BaseModel):
    """Response containing sunshine location recommendations and metadata."""

    query: dict = Field(
        ..., description="Query parameters used for the recommendation request"
    )
    results: List[Recommendation] = Field(
        ..., description="List of recommended locations ordered by score"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when response was generated",
    )
    version: str = Field("v1", description="API version for compatibility tracking")
