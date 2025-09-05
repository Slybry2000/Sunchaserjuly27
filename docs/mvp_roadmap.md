# Sun Chaser — MVP Roadmap & Status

## Project Status: Phase B - Production Polish 🚀

✅ **Core MVP Complete** - Weather data engine and UI functional  
✅ **Unsplash Integration** - Professional photo experience with API compliance  
✅ **CI/CD Pipeline** - 16/16 automated tests passing (PR #9)  
🎯 **Current Phase**: Screenshot capture and Unsplash application submission

---

## Objective

Launch a production-ready "clear skies" discovery app with professional photo experience and weather-aware recommendations.

## ✅ Sprint 0 — Setup & Foundation (COMPLETE)

- [x] Create project environment (Firebase or minimal VPS) and repo scaffolding
- [x] Register 2–3 weather forecast APIs (Open‑Meteo / OpenWeatherMap / Weatherbit) and record keys in `.env`
- [x] Acquire and upload a small U.S. locations dataset (GeoNames/SimpleMaps) or use `data/pnw.csv` for initial testing
- [x] Verify local dev run: `uvicorn main:app --reload`

**Success**: ✅ Firebase/APIs ready or local backend runs; dataset accessible One‑page MVP Roadmap

Objective

Launch a scrappy MVP for “clear skies” discovery quickly with minimal cost and fast execution.

Sprint 0 — Setup & Foundation (1–2 days)

- Create project environment (Firebase or minimal VPS) and repo scaffolding
- Register 2–3 weather forecast APIs (Open‑Meteo / OpenWeatherMap / Weatherbit) and record keys in `.env`
- Acquire and upload a small U.S. locations dataset (GeoNames/SimpleMaps) or use `data/pnw.csv` for initial testing
- Verify local dev run: `uvicorn main:app --reload`

Success: Firebase/APIs ready or local backend runs; dataset accessible

## ✅ Sprint 1 — Forecast Data Engine (COMPLETE)

- [x] Implement a backend task (Python script or Cloud Function) to fetch forecasts for ~100 locations
- [x] Normalize cloud cover and temperature into a simple slot shape
- [x] Compute a simple Sun Confidence Score (agreement or weighted average across providers / or single provider with heuristics)
- [x] Persist processed forecast & score to a datastore (Firestore or local JSON/SQLite)
- [x] Add a small set of tests for parsing and scoring

**Success**: ✅ Forecast data stored; manual verification of Sun Confidence values

## ✅ Sprint 2 — UI MVP (COMPLETE)

- [x] Minimal Flutter (or FlutterFlow) UI with:
  - [x] Location input (lat/lon or query)
  - [x] Radius selector and date picker
  - [x] "Find Clear Skies" action that displays a ranked list
- [x] Results screen: list of locations with Sun Confidence, cloud%, brief forecast
- [x] Use dummy data first, then switch to live data

**Success**: ✅ Basic user flow works with test data

## ✅ Sprint 3 — Integration & Polish (COMPLETE)

- [x] Connect frontend to backend or Firestore
- [x] Implement error handling and empty-state UX
- [x] Add ETag/304 handling on backend and basic client caching for repeated queries

**Success**: ✅ End‑to‑end search with live data and caching behavior

## ✅ Sprint 4 — Unsplash Integration (COMPLETE) 

**🎯 Major Achievement: Professional Photo Experience with Full CI/CD**

- [x] **Backend API Implementation**
  - [x] Photo tracking endpoint (`/internal/photos/track`) with deduplication
  - [x] Attribution helper service for proper photographer crediting
  - [x] Production safety hardening with environment gating
- [x] **CI/CD Pipeline** 
  - [x] Automated testing (16/16 checks passing ✅)
  - [x] Integration smoke testing with mock header security
  - [x] Code quality enforcement (linting, type checking)
- [x] **Production Safety**
  - [x] Mock header hardening for CI testing
  - [x] Environment variable gating (`ALLOW_TEST_HEADERS`)
  - [x] Secret validation (`UNSPLASH_TEST_HEADER_SECRET`)
- [x] **Documentation & Compliance**
  - [x] Complete implementation guides and API documentation
  - [x] Unsplash application checklist and submission preparation
  - [x] Security audit and best practices implementation

**Success**: ✅ **PR #9 with full green CI status** - Ready for Unsplash application

---

## 🎯 Phase B — Production Polish (CURRENT)

### Next Immediate Steps (Priority Order)

1. **📸 Screenshot Capture** (1-2 days)
   - [ ] Take required Unsplash application screenshots
   - [ ] Demonstrate proper attribution and UI distinction
   - [ ] Capture photo integration examples

2. **🔗 Frontend Polish** (1 day)  
   - [ ] Implement `url_launcher` for tappable attribution links
   - [ ] Final UI polish and accessibility improvements

3. **📋 Application Submission** (1-2 weeks review)
   - [ ] Submit to Unsplash Developer Portal
   - [ ] Respond to any review feedback
   - [ ] Gain production API access (5,000 requests/hour)

4. **🚀 Production Deployment** (2-3 days)
   - [ ] Deploy with production Unsplash API keys
   - [ ] Monitor rate limits and usage analytics  
   - [ ] Set up production observability dashboard

---

## Production DoD ✅ ACHIEVED

- [x] **API Endpoints**: `/recommend` returns ranked results with ETag caching
- [x] **CI/CD**: Automated testing with 16/16 checks passing 
- [x] **Observability**: Request ID, structured logging, and metrics instrumentation
- [x] **Photo Integration**: Professional Unsplash API integration with proper attribution
- [x] **Production Safety**: Security hardening and environment protection
- [x] **Documentation**: Complete implementation and integration guides

---

## Technical Notes

- **Full engineering plan**: Detailed cache semantics, SWR, single‑flight, pytest config in `docs/plan_vertical_slice.md`
- **GitHub Issues**: Issue drafts in `issues/` folder can be converted via `gh` CLI or created manually
- **Current Achievement**: **Phase A (MVP) Complete** ✅ | **Phase B (Production Polish)** In Progress 🎯
