import importlib
import logging

from fastapi.testclient import TestClient


def _reload_app():
    # Reload the backend module and the top-level shim so environment changes
    # to CORS_ALLOWED_ORIGINS are picked up.
    import Backend.main as backend_main
    import main as top_main
    importlib.reload(backend_main)
    importlib.reload(top_main)
    from main import app
    return app


def test_cors_allows_configured_origin(monkeypatch):
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', 'https://allowed.example')
    app = _reload_app()
    client = TestClient(app)

    resp = client.get('/health', headers={'Origin': 'https://allowed.example'})
    assert resp.status_code == 200
    # CORSMiddleware should echo the allowed Origin back
    assert resp.headers.get('access-control-allow-origin') == 'https://allowed.example'


def test_cors_logs_rejected_origin(monkeypatch, caplog):
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', 'https://allowed.example')
    app = _reload_app()
    client = TestClient(app)

    caplog.set_level(logging.WARNING, logger='sunshine_backend')

    # Send a request from a different origin; the server should not include
    # Access-Control-Allow-Origin header and should emit a warning log.
    resp = client.get('/health', headers={'Origin': 'https://evil.example'})
    assert resp.status_code == 200
    assert resp.headers.get('access-control-allow-origin') is None

    # Check that the warning log was recorded
    messages = [r.getMessage() for r in caplog.records]
    # Log message was changed to a structured-ish message 'Rejected CORS origin'
    assert any('Rejected CORS origin' in m for m in messages)
