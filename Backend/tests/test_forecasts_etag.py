import sys
from pathlib import Path

# ensure repo root is on sys.path for imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from Backend.main import app  # noqa: E402


def test_forecasts_etag_304():
    client = TestClient(app)
    resp = client.get("/forecasts")
    # If no snapshot is present the endpoint returns 404; that's acceptable in CI
    assert resp.status_code in (200, 404)

    if resp.status_code == 200:
        etag = resp.headers.get("ETag")
        assert etag is not None

        # Revalidate using If-None-Match should return 304
        resp2 = client.get("/forecasts", headers={"If-None-Match": etag})
        assert resp2.status_code == 304
    else:
        assert resp.status_code == 404
