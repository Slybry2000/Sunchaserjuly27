import sys
from pathlib import Path

# ensure repo root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from Backend.main import app  # noqa: E402


def test_internal_forecasts_endpoint():
    client = TestClient(app)
    # call without filters
    resp = client.get("/internal/forecasts")
    assert resp.status_code in (200, 404)

    # call with lat/lon/top (if no snapshot, still expect 404)
    resp2 = client.get(
        "/internal/forecasts", params={"lat": 47.6, "lon": -122.3, "top": 5}
    )
    if resp2.status_code == 200:
        body = resp2.json()
        assert "source" in body and "count" in body and "items" in body
        assert isinstance(body["items"], list)
        # items should be at most top
        assert body["count"] <= 5
        # check ordering by score desc
        scores = [float(it.get("score", 0)) for it in body["items"]]
        assert scores == sorted(scores, reverse=True)
    else:
        assert resp2.status_code == 404
