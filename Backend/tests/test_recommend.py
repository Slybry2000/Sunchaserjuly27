from fastapi.testclient import TestClient
from main import app
import routers.recommend as recommend_module

def test_recommend_happy(monkeypatch):
    client = TestClient(app)
    # Patch weather and scoring to avoid real HTTP
    async def _fake_rank(*args, **kwargs):
        return []

    # Patch the rank used by the router so no real weather/scoring runs occur
    monkeypatch.setattr(recommend_module, "rank", _fake_rank)
    response = client.get("/recommend?lat=46.8&lon=-121.7&radius=100")
    assert response.status_code in (200, 404)  # 404 if no locations in radius
    if response.status_code == 200:
        assert "ETag" in response.headers
        assert "recommendations" in response.json()

def test_recommend_missing_param():
    client = TestClient(app)
    response = client.get("/recommend?lat=46.8")
    assert response.status_code == 422
