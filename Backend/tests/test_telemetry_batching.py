import json
import time
from fastapi.testclient import TestClient
from Backend.main import app


def test_telemetry_batching_writes_jsonl(tmp_path, monkeypatch):
    sink_file = tmp_path / 'telemetry_batch.jsonl'
    monkeypatch.setenv('TELEMETRY_SINK_PATH', str(sink_file))
    monkeypatch.setenv('TELEMETRY_BATCH_SIZE', '2')
    monkeypatch.setenv('TELEMETRY_BATCH_INTERVAL_SEC', '1')

    client = TestClient(app)

    # post two events quickly; batcher configured to flush at size=2
    r1 = client.post('/telemetry', json={'event': 'batch1', 'properties': {}})
    assert r1.status_code == 202
    r2 = client.post('/telemetry', json={'event': 'batch2', 'properties': {}})
    assert r2.status_code == 202

    # allow some time for batcher to flush
    time.sleep(1.5)

    assert sink_file.exists()
    lines = sink_file.read_text(encoding='utf-8').splitlines()
    assert len(lines) >= 2
    parsed = [json.loads(line) for line in lines]
    names = {p.get('event') for p in parsed}
    assert 'batch1' in names and 'batch2' in names
