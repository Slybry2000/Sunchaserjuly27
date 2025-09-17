# Sun Chaser - Weather-Aware Outdoor Recreation Discovery

![Flutter CI](https://github.com/Slybry2000/Sunchaserjuly27/actions/workflows/flutter_ci.yml/badge.svg?branch=feature/unsplash-tracking)
![Python Tests](https://github.com/Slybry2000/Sunchaserjuly27/actions/workflows/ci-tests.yml/badge.svg?branch=feature/unsplash-tracking)
![Lint & Type](https://github.com/Slybry2000/Sunchaserjuly27/actions/workflows/ci-lint.yml/badge.svg?branch=feature/unsplash-tracking)
![Integration Smoke](https://github.com/Slybry2000/Sunchaserjuly27/actions/workflows/integration-smoke.yml/badge.svg?branch=feature/unsplash-tracking)

A production-ready mobile application and FastAPI backend for discovering outdoor recreation locations with weather-aware recommendations and professional photography.

## 🎯 Status: September 2025 - Production Ready

### ✅ **MAJOR MILESTONE: Full Implementation Complete**
**🚀 PR #9: 16/16 CI Checks Passing** - All automated testing green  
**🎯 READY FOR**: Unsplash production API application submission  
**📊 ACHIEVEMENT**: Complete weather + photo integration with production safety

### ✅ **Phase A-C Complete: Production Implementation**
- **✅ Phase A**: Complete weather-based recommendation engine
- **✅ Phase B**: Comprehensive testing and CI/CD (16/16 passing)  
- **✅ Phase C**: Frontend reliability and Flutter app polish
- **✅ Phase D**: **Unsplash API Integration Complete** *(Major Achievement)*

### 🌟 **Unsplash Integration Achievement**
- **✅ Backend API Complete**: Photo tracking with deduplication
- **✅ Attribution System**: Proper photographer crediting
- **✅ Production Safety**: Security hardening with CI validation
- **✅ CI/CD Pipeline**: Automated testing with mock header security
- **✅ Documentation**: Complete implementation and application guides

### 🎯 **Current Phase: Application Submission**
- **Next Step**: Submit Unsplash production API application
- **Timeline**: 1-2 weeks for Unsplash review process
- **Goal**: Gain 5,000 requests/hour production API access
- **Status**: All technical requirements complete and validated

## Key Features Delivered ✅

### 🌦️ **Weather-Based Recommendation Engine**
- **Complete `/recommend` API**: Weather-based sunny location recommendations
- **Weather Integration**: Open-Meteo API with caching and error handling  
- **In-Process SWR Cache**: Stale-while-revalidate with single-flight protection
- **Deterministic ETags**: Strong caching with SHA-256 hashes
- **PNW Location Dataset**: 103+ curated locations with validation

### 📸 **Professional Photo Integration**
- **Unsplash API Integration**: Location-specific outdoor photography
- **Download Tracking**: Backend endpoint with deduplication (`/internal/photos/track`)
- **Attribution System**: "Photo by [Photographer] on Unsplash" with tappable links
- **Production Safety**: Mock header hardening and environment gating
- **Cost Effective**: $0 vs. $165-550 for stock photos

### 🧪 **Production Quality & Testing**
- **Comprehensive Testing**: 16/16 CI checks passing with full automation
- **Integration Smoke Tests**: End-to-end API flow validation
- **Code Quality**: Automated linting, type checking, and formatting
- **Security Hardening**: Environment protection and secret validation

### 📱 **Flutter Mobile App**
- **Production-ready**: Complete mobile app with error handling
- **Image Management**: Category-based fallbacks with Unsplash integration
- **ETag Caching**: Client-side caching with backend coordination
- **Weather UI**: Location cards with Sun Confidence scoring

### 🔧 **Production Infrastructure**
- **Observability**: Structured JSON logs, request IDs, latency tracking  
- **CI/CD Pipeline**: GitHub Actions with automated testing and deployment
- **Documentation**: Complete API docs, integration guides, and examples
- **Monitoring**: Success/failure metrics and production dashboards ready

## 📸 Photo Integration: Production Ready

### ✅ **Current Implementation - Complete**
- **Unsplash API Integration**: Full backend implementation with production safety
- **Professional Photography**: High-quality outdoor recreation imagery
- **Download Tracking**: Required backend endpoint (`/internal/photos/track`)
- **Attribution System**: Server-side HTML generation with tappable links
- **Deduplication**: Prevents duplicate tracking with TTL cache

### ✅ **Production Compliance**
- **Proper Attribution**: "Photo by [Photographer] on Unsplash" format
- **Link Requirements**: Photographer profile and Unsplash photo page links
- **Download Tracking**: Backend calls Unsplash download endpoint for every view
- **Photo Hotlinking**: Direct Unsplash URL usage (never stored locally)
- **Rate Limiting**: Prepared for 5,000 requests/hour production limits

### ✅ **Technical Implementation Status**
- **Backend Endpoints**: `/internal/photos/meta` and `/internal/photos/track`
- **CI/CD Integration**: 16/16 automated tests passing in GitHub Actions
- **Security Hardening**: Mock header validation and environment gating
- **Documentation**: Complete API documentation and integration examples
- **Application Ready**: All materials prepared for Unsplash submission

**Next Step**: Submit Unsplash production API application using materials in `docs/UNSPLASH_APPLICATION_MATERIALS.md`

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

Note: The PNW dataset includes demo rows (ids 101–103) near Seattle for local development and testing.

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

### Seed forecast snapshot DB (local)
Run the fetch job to write a JSON snapshot and persist a local SQLite DB used by the internal snapshot API.

```powershell
# Activate the virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# Run the fetch script (will write data/forecast_snapshot.json and data/forecast_snapshot.db)
python Backend\scripts\fetch_forecasts.py
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

| Endpoint                    | Method | Description                                 | Status         |
|----------------------------|--------|---------------------------------------------|----------------|
| `/health`                  | GET    | Health check                               | ✅ Complete     |
| `/geocode`                 | GET    | Convert location query to lat/lon           | ✅ Complete     |
| `/recommend`               | GET    | Get ranked sunny location recommendations   | ✅ Complete     |
| `/forecasts`               | GET    | Get forecast snapshot data                  | ✅ Complete     |
| `/internal/photos/meta`    | GET    | Get photo metadata with attribution         | ✅ Complete     |
| `/internal/photos/track`   | POST   | Track photo views (Unsplash compliance)     | ✅ Complete     |
| `/docs`                    | GET    | Interactive API documentation               | ✅ Complete     |

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

#### `/forecasts` Example

```bash
curl "http://127.0.0.1:8001/forecasts"
```

Sample response:

```json
{
  "forecasts": [
    {
      "id": 1,
      "location_name": "Mount Rainier",
      "lat": 46.8523,
      "lon": -121.7603,
      "forecast_data": {...}
    }
  ],
  "generated_at": "2025-08-12T05:22:31Z",
  "etag": "forecast_etag"
}
```

**Features:**
- Snapshot of forecast data
- ETag for caching
- SQLite backend with JSON fallback

#### Quick ETag Flow Example

```bash
# First request - 200 OK with ETag
curl -i "http://127.0.0.1:8001/recommend?lat=47.6&lon=-122.3&radius=100"
# HTTP/1.1 200 OK
# ETag: "abc123etag"
# Cache-Control: public, max-age=900, stale-while-revalidate=300

# Second request with If-None-Match - 304 Not Modified
curl -i -H 'If-None-Match: "abc123etag"' "http://127.0.0.1:8001/recommend?lat=47.6&lon=-122.3&radius=100"
# HTTP/1.1 304 Not Modified
# ETag: "abc123etag"
```

This demonstrates client-side caching using ETags.

## 🧪 Testing - Production Quality

### ✅ **Current Test Status: 16/16 CI Checks Passing**
```bash
# Run all tests
pytest

# Run with verbose output  
pytest -vv

# Run specific test suite
pytest Backend/tests/test_unsplash_router.py -v
```

### **Comprehensive Test Coverage**
- **✅ API Integration Tests**: All endpoints including new Unsplash integration
- **✅ Weather Service Tests**: Upstream API mocking and error handling
- **✅ Cache Operations**: SWR cache, TTL, LRU eviction, single-flight protection
- **✅ HTTP Caching**: ETag/304 behavior and client-side caching
- **✅ Unsplash Integration**: Photo tracking, attribution, and deduplication
- **✅ Security Tests**: Mock header validation and environment protection
- **✅ Error Handling**: Observability middleware and graceful failures

### **CI/CD Pipeline Status**
- **Python Tests**: ✅ Unit and integration test suite  
- **Integration Smoke**: ✅ End-to-end API flow validation
- **Lint & Type**: ✅ Code quality (Ruff + MyPy)  
- **Flutter CI**: ✅ Frontend analysis and testing
- **Security**: ✅ Production safety validation

### **Frontend Testing**
- **Widget Tests**: Loading states, error handling, image management
- **Integration Tests**: Backend API communication and ETag caching
- **UI Tests**: Attribution display and link functionality

## Pre-commit (developer)

We use `pre-commit` to auto-run linters and formatters locally. To enable it:

```bash
pip install pre-commit
pre-commit install
```

The repository includes a `.pre-commit-config.yaml` that runs `ruff --fix` so
unused imports and simple style fixes are applied automatically before commits.


## 🏗️ Architecture - Production Ready

### **Complete Implementation Stack**
```
Sun Chaser Mobile App (Flutter)
├── Location Discovery UI with weather-aware recommendations
├── Professional photo integration with Unsplash API  
├── Proper attribution display with tappable links
└── Client-side ETag caching for performance

FastAPI Backend (Production Ready)
├── /health                    # Health check endpoint
├── /geocode                   # Geocoding with Mapbox API  
├── /recommend                 # ✅ Weather-based recommendations
├── /forecasts                 # Forecast snapshot data
├── /internal/photos/meta      # ✅ Photo metadata with attribution
├── /internal/photos/track     # ✅ Unsplash download tracking
├── Backend/
│   ├── services/
│   │   ├── weather.py             # ✅ Open-Meteo integration
│   │   ├── locations.py           # ✅ PNW dataset management  
│   │   ├── scoring.py             # ✅ Sun Confidence algorithm
│   │   ├── geocode.py             # Mapbox integration
│   │   └── unsplash_integration.py # ✅ Photo API integration
│   ├── routers/
│   │   ├── recommend.py           # Weather recommendation endpoints
│   │   └── unsplash.py            # ✅ Photo tracking endpoints
│   ├── utils/
│   │   ├── cache_inproc.py        # ✅ SWR cache with single-flight
│   │   ├── etag.py                # ✅ Deterministic ETag generation
│   │   └── geo.py                 # ✅ Geographic utilities
│   ├── middleware/
│   │   └── observability.py       # ✅ Structured logging
│   ├── scripts/
│   │   └── integration_smoke.py   # ✅ End-to-end testing
│   ├── tests/                     # ✅ 16/16 CI checks passing
│   └── data/pnw.csv              # ✅ Curated location dataset
```

### **Production Infrastructure**
- **CI/CD Pipeline**: GitHub Actions with 16/16 automated checks
- **Security Hardening**: Environment gating and mock header validation  
- **Monitoring**: Structured logging, metrics, and observability ready
- **Documentation**: Complete API docs and integration guides
- **Deployment**: Docker containerization and cloud deployment ready

### Caching Strategy - Optimized
- **In-Process SWR Cache**: LRU+TTL with stale-while-revalidate and single-flight protection
- **Photo Deduplication**: TTL-based tracking prevention for Unsplash compliance
- **ETag Caching**: Client-side HTTP caching with SHA-256 deterministic ETags
- **No External Dependencies**: All caching in-process for simplicity and cost efficiency
- **TTL Configuration**: 20 minutes for weather, 7 days for geocoding, configurable photo dedupe
- **Graceful Degradation**: API functionality maintained without cache

## 🔐 Security & Production Features

### **Environment Protection**
- **Secret Management**: Secure API key storage with environment variables
- **Mock Header Hardening**: CI testing with `ALLOW_TEST_HEADERS` gating
- **Input Validation**: Comprehensive query parameter and request validation  
- **Error Handling**: No sensitive data exposure in error responses
- **HTTPS Ready**: TLS termination at deployment level

### **Production Safety** 
- **CI/CD Validation**: 16/16 automated checks including security tests
- **Environment Gating**: Prevents accidental test behavior in production
- **Audit Logging**: Structured logs for monitoring and debugging
- **Rate Limiting**: Prepared for API rate limits and graceful handling
- **Monitoring Ready**: Metrics instrumentation for production dashboards

## � Next Steps: Production Deployment

### **Phase E: Unsplash Application & Launch** (Current)
**Priority**: Submit Unsplash production API application  
**Timeline**: 1-2 weeks for review process  
**Materials**: Complete application package in `docs/UNSPLASH_APPLICATION_MATERIALS.md`

### **Phase F: Production Launch** (Next)
1. **Post-Approval**: Deploy with production Unsplash API keys
2. **Monitoring**: Set up production dashboards and alerting  
3. **Performance**: Monitor rate limits and optimize photo loading
4. **User Feedback**: Collect usage data and iterate on recommendations

### **Future Enhancements**
- **Advanced Photo Selection**: Location-specific search algorithms
- **User-Generated Content**: Community photo uploads and validation
- **Expanded Regions**: Beyond Pacific Northwest to national coverage
- **Weather Improvements**: Multi-provider aggregation and machine learning

## 📚 Documentation & Resources

### **Technical Documentation**
- **API Documentation**: Visit `http://127.0.0.1:8001/docs` for interactive Swagger docs
- **Implementation Guides**: Complete integration documentation in `docs/` folder
- **Unsplash Integration**: `docs/UNSPLASH_APPLICATION_MATERIALS.md` 
- **Development Setup**: `docs/DEVELOPMENT.md`
- **Testing Guide**: `docs/dev-testing.md`

### **Project Resources**
- **GitHub Repository**: https://github.com/Slybry2000/Sunchaserjuly27
- **Current Branch**: `feature/unsplash-tracking` (PR #9 - 16/16 checks passing)
- **Production Roadmap**: `docs/mvp_roadmap.md`
- **Architecture Details**: `docs/plan_vertical_slice.md`

## Attribution

You can paste either of the following lines into the README, app footer, or UI:

```
Weather data provided by Open-Meteo (https://open-meteo.com)
```

Shorter footer-friendly option:

```
Weather data © Open-Meteo
```
