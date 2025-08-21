from fastapi.testclient import TestClient
from main import app

from services.weather import WeatherError

from routers.recommend import get_weather_dep

def test_recommend_weather_error():
    # Dependency override for get_weather
    async def fail_weather(lat, lon):
        raise WeatherError("weather fail")
    app.dependency_overrides[get_weather_dep] = lambda: fail_weather
    client = TestClient(app)
    response = client.get("/recommend?lat=46.8&lon=-121.7&radius=100")
    assert response.status_code == 502
    assert "Weather service unavailable" in response.json()["detail"]
    app.dependency_overrides = {}
