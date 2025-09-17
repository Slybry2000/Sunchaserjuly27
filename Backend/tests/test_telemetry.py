from fastapi.testclient import TestClient

from Backend.main import app


def test_telemetry_ingest(tmp_path):
    client = TestClient(app)
    payload = {"event": "test_event", "properties": {"foo": "bar"}}
    r = client.post("/telemetry", json=payload)
    assert r.status_code == 202
    data = r.json()
    assert data.get("status") == "accepted"

    # Recent endpoint should include our event
    r2 = client.get("/telemetry/recent")
    assert r2.status_code == 200
    body = r2.json()
    assert body["count"] >= 1
    events = body["events"]
    assert any(e.get("event") == "test_event" for e in events)
