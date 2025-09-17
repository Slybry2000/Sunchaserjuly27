from fastapi.testclient import TestClient

from main import app


def test_request_id_header():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0
