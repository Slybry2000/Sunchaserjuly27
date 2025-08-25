import asyncio
import types
from Backend.services.telemetry_sink import sink_event_forward_http
from Backend.services.metrics import get_metrics, reset


class DummyClient:
    def __init__(self, fail_times=2):
        self._fail_times = fail_times

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None):
        if self._fail_times > 0:
            self._fail_times -= 1
            raise RuntimeError('simulated transient error')
        return types.SimpleNamespace(status_code=200)


async def _run_forward(monkeypatch):
    # simulate failing twice then succeed
    dummy = DummyClient(fail_times=2)

    async def _dummy_client_factory(timeout=None):
        return dummy

    monkeypatch.setenv('TELEMETRY_SINK_URL', 'http://example.invalid/telemetry')
    monkeypatch.setenv('TELEMETRY_FORWARD_RETRIES', '4')
    # patch httpx.AsyncClient to return our dummy client
    monkeypatch.setattr('Backend.services.telemetry_sink.httpx.AsyncClient', lambda timeout=None: dummy)

    reset()
    await sink_event_forward_http({'event': 'retry_test'})
    # expose metrics after run
    return get_metrics()


def test_forward_retries(monkeypatch):
    metrics = asyncio.get_event_loop().run_until_complete(_run_forward(monkeypatch))
    # We expect at least 3 attempts (fail, fail, success) and 1 success
    assert metrics.get('telemetry_forward_attempts', 0) >= 3
    assert metrics.get('telemetry_forward_success', 0) >= 1
