import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_recommend_q_dev_bypass_returns_demo_rows(monkeypatch):
    """With DEV_BYPASS_SCORING=true and ENABLE_Q=true, a text q query should
    return nearby demo rows (the dev dataset entries appended in this branch).
    This test runs the FastAPI app via ASGI using the project's main app.
    """
    # Set dev env flags for the test run
    monkeypatch.setenv("ENABLE_Q", "true")
    monkeypatch.setenv("DEV_BYPASS_SCORING", "true")
    monkeypatch.setenv("DEV_ALLOW_GEOCODE", "true")

    # Import app after env mutated
    from Backend.main import app

    # Use ASGI transport where available to run the app in-process.
    try:
        from httpx import ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            resp = await ac.get("/recommend?q=Seattle, WA&radius=25")
    except Exception:
        # Fallback: use TestClient from starlette (sync) if ASGITransport not available
        from starlette.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/recommend?q=Seattle, WA&radius=25")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Expect results to contain at least one of the demo ids we added (101..103)
        ids = {r.get("id") for r in body.get("results", [])}
        assert ids & {"101", "102", "103"}, "Expected demo ids in results"
