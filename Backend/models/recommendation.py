from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Recommendation(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    distance_mi: float
    sun_start_iso: Optional[str] = None  # explicit ISO string
    duration_hours: int = 0
    score: float

class RecommendResponse(BaseModel):
    query: dict
    results: List[Recommendation]
    generated_at: datetime = Field(default_factory=datetime.utcnow)  # UTC
    version: str = "v1"
