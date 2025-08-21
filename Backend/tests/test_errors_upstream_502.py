import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient  # type: ignore
from main import app
from Backend.models.errors import UpstreamError


def _raise_upstream():
    raise UpstreamError("Open-Meteo unavailable")

# Add a test-only route to trigger the handler once
if not any(getattr(r, "path", "") == "/__raise_upstream" for r in app.router.routes):
    app.add_api_route("/__raise_upstream", _raise_upstream, methods=["GET"])

client = TestClient(app)


def test_upstream_error_maps_to_502():
    resp = client.get("/__raise_upstream")
    assert resp.status_code == 502
    data = resp.json()
    assert data["error"] == "upstream_error"
    assert "unavailable" in data["detail"]
