from pydantic import BaseModel
from typing import Optional

class ErrorPayload(BaseModel):
    error: str
    detail: str
    hint: Optional[str] = None

# Error taxonomy for Phase B
class UpstreamError(Exception):
    pass

class LocationNotFound(Exception):
    pass

class SchemaError(Exception):
    pass

class TimeoutBudgetExceeded(Exception):
    pass
