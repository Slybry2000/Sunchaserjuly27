# Sunshine Backend API

A FastAPI-based service for finding sunny locations using weather data and geocoding.

## 🎯 Current Status: Sprint 1 Complete

**✅ Sprint 0**: Project skeleton, FastAPI health endpoint, Docker, CI/CD  
**✅ Sprint 1**: Geocoding service with Mapbox integration and Redis caching  
**🔄 Next**: Sprint 2 - Weather data integration with OpenWeatherMap

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Clone and navigate to project
cd c:\Users\bpiar\Projects\Sunchaserjuly27

# Activate virtual environment 
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
copy .env.template .env

# Edit .env with your API keys:
# MAPBOX_TOKEN=your_mapbox_token_here
# REDIS_URL=your_upstash_redis_url  (optional, for production)
# REDIS_TOKEN=your_upstash_redis_token  (optional, for production)
```

### 3. Run the Server
```bash
# Development server with auto-reload
uvicorn main:app --reload --port 8001

# Production server
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 4. Test the API
```bash
# Health check
curl http://127.0.0.1:8001/health

# Geocoding (requires MAPBOX_TOKEN in environment)
curl "http://127.0.0.1:8001/geocode?q=Seattle,WA"
```

## 📚 API Documentation

Visit `http://127.0.0.1:8001/docs` for interactive Swagger documentation.


### Available Endpoints

| Endpoint      | Method | Description                                 | Status         |
|---------------|--------|---------------------------------------------|----------------|
| `/health`     | GET    | Health check                               | ✅ Complete     |
| `/geocode`    | GET    | Convert location query to lat/lon           | ✅ Complete     |
| `/recommend`  | GET    | Get ranked sunny location recommendations   | ✅ Phase A Slice|
| `/docs`       | GET    | Interactive API documentation               | ✅ Complete     |

#### `/recommend` Example

```bash
curl "http://127.0.0.1:8001/recommend?lat=47.6&lon=-122.3&radius=100"
```

Sample response:

```json
{
	"recommendations": [
		{
			"location": {
				"id": 1,
				"name": "Mount Rainier",
				"lat": 46.8523,
				"lon": -121.7603,
				"elevation": 4392.0,
				"category": "Mountain",
				"state": "WA",
				"timezone": "America/Los_Angeles"
			},
			"score": 87.5,
			"best_window": {
				"time": "2025-08-12T14:00",
				"temperature_2m": 19.5,
				"cloudcover": 10.0,
				"precipitation_probability": 0.0
			}
		}
	],
	"etag": "abc123etag"
}
```

**Features:**
- In-process SWR cache for weather
- Deterministic ETag for caching
- Structured logs, request ID, and latency
- Location dataset with radius filtering
- Sunshine scoring and ranking

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_geocode.py -v

# Run with coverage
pytest --cov=. tests/
```

**Current Test Coverage**: 7/7 tests passing
- Health endpoint tests
- Geocoding service unit tests  
- Geocoding endpoint integration tests

## 🏗️ Architecture

### Current Implementation (Sprint 1)
```
FastAPI Application
├── /health          # Health check endpoint
├── /geocode         # Geocoding with Mapbox API
├── services/
│   └── geocode.py   # Mapbox integration
├── utils/
│   └── cache.py     # Redis caching (with local fallback)
└── tests/           # Comprehensive test suite
```

### Caching Strategy
- **Redis**: Production caching with Upstash
- **Local Fallback**: Development without Redis dependency
- **TTL**: 7 days for geocoding results
- **Graceful Degradation**: API works without cache

## 🐳 Docker Deployment

```bash
# Build container
docker build -t sunshine-api .

# Run locally
docker run -p 8080:8080 -e MAPBOX_TOKEN=your_token sunshine-api

# Deploy to Cloud Run (see deployment guide)
```

## 🔐 Security Features

- **Environment Variables**: Secure API key storage
- **Error Handling**: No sensitive data in error responses  
- **Input Validation**: Query parameter validation
- **HTTPS Ready**: TLS termination at Cloud Run level

## 📈 Performance

- **Async Operations**: Non-blocking HTTP requests
- **Redis Caching**: Sub-millisecond cache hits
- **Connection Pooling**: httpx.AsyncClient reuse
- **Graceful Timeouts**: 10s timeout for external APIs

## 🔧 Development

### Project Structure
```
├── .github/workflows/ci.yml    # GitHub Actions CI
├── services/geocode.py         # ✅ Mapbox geocoding
├── utils/cache.py             # ✅ Redis caching utilities  
├── tests/                     # ✅ Comprehensive tests
├── .env.template             # Environment configuration
├── Dockerfile                # Container configuration
├── main.py                   # ✅ FastAPI app with endpoints
├── pyproject.toml           # ✅ Pytest configuration
└── requirements.txt         # ✅ All dependencies
```

### Adding New Features
1. Create service in `services/` directory
2. Add endpoint to `main.py` 
3. Write tests in `tests/`
4. Update this README

## 🚀 Next Sprint: Weather Integration

The foundation is ready for Sprint 2 implementation:
- OpenWeatherMap API integration
- Weather forecast parsing
- Sunshine scoring algorithm
- Location database with distance filtering

## 📋 Sprint Progress

See `docs/sprint_progress.md` for detailed implementation tracking.
