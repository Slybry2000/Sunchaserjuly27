import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient  # type: ignore
from main import app
from models.errors import LocationNotFound, TimeoutBudgetExceeded
from fastapi import APIRouter

# Define test-only endpoints to trigger handlers
router = APIRouter()

@router.get("/__raise_404")
async def _raise_404():
    raise LocationNotFound("No matching location")

@router.get("/__raise_504")
async def _raise_504():
    raise TimeoutBudgetExceeded("Request timed out")

# Mount router once
if not any(getattr(r, "path", "") == "/__raise_404" for r in app.router.routes):
    app.include_router(router)

client = TestClient(app)

def test_location_not_found_maps_to_404():
    resp = client.get("/__raise_404")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"] == "location_not_found"
    assert "No matching" in data["detail"]


def test_timeout_budget_exceeded_maps_to_504():
    resp = client.get("/__raise_504")
    assert resp.status_code == 504
    data = resp.json()
    assert data["error"] == "timeout_budget_exceeded"
    assert "timed out" in data["detail"]
