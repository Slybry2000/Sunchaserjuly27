from starlette.testclient import TestClient


def test_beta_gate_enforced(monkeypatch):
    # Configure a single allowed key BEFORE importing the app so middleware is
    # created during FastAPI app construction.
    monkeypatch.setenv('BETA_KEYS', 'alpha123')

    # Import app after env is set
    from Backend.main import app

    client = TestClient(app)

    # Missing header -> 401
    r = client.get('/recommend')
    assert r.status_code == 401
    assert r.json().get('error') == 'beta_key_required'

    # Invalid header -> 401
    r = client.get('/recommend', headers={'X-Beta-Key': 'wrong'})
    assert r.status_code == 401
    assert r.json().get('error') == 'beta_key_invalid'

    # Valid header -> 422 or 200 depending on route validation; we only assert not 401
    r = client.get('/recommend', headers={'X-Beta-Key': 'alpha123'})
    assert r.status_code != 401

    # Health endpoint is exempt
    r = client.get('/health')
    assert r.status_code == 200
