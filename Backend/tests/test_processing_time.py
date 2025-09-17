from fastapi.testclient import TestClient

from main import app


def test_processing_time_header():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Processing-Time" in response.headers
    assert int(response.headers["X-Processing-Time"]) >= 0
