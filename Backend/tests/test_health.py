from fastapi.testclient import TestClient

from main import app

c = TestClient(app)


def test_health():
    assert c.get("/health").json() == {"status": "ok"}
