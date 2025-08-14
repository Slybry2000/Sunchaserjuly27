import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_recommend_happy_path():
    resp = client.get("/recommend?lat=47.6&lon=-122.3")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert isinstance(data["results"], list)

def test_recommend_radius_clamp():
    resp = client.get("/recommend?lat=47.6&lon=-122.3&radius=1000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"]["radius"] <= 300

def test_recommend_q_disabled():
    resp = client.get("/recommend?q=Seattle")
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "geocoding_disabled"
