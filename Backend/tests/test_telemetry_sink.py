import os
import json
import time
from fastapi.testclient import TestClient
from Backend.main import app


def test_telemetry_sink_writes_jsonl(tmp_path, monkeypatch):
    sink_file = tmp_path / 'telemetry.jsonl'
    monkeypatch.setenv('TELEMETRY_SINK_PATH', str(sink_file))

    client = TestClient(app)
    payload = {'event': 'sink_test', 'properties': {'x': 1}}
    r = client.post('/telemetry', json=payload)
    assert r.status_code == 202

    # allow a small moment for background task to write (sink uses asyncio.to_thread)
    time.sleep(0.2)

    assert sink_file.exists()
    lines = sink_file.read_text(encoding='utf-8').splitlines()
    assert len(lines) >= 1
    parsed = [json.loads(l) for l in lines]
    assert any(p.get('event') == 'sink_test' for p in parsed)
