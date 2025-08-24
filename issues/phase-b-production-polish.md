---
name: Phase B — Production Polish
labels: [phase-b, backend, production]
---

# Phase B — Production Polish

## Completed Tasks ✅

### 1. Conditional Requests
- [x] Implement `If-None-Match` handling in router
- [x] Tests: 304 response, invariance with identical inputs
- [x] ETag stability and roundtrip behavior verification

### 2. Dataset Expansion
- [x] Expand dataset from ~50 to 100 unique PNW locations
- [x] Add comprehensive metadata: category, elevation, state, timezone
- [x] Update Pydantic models (`Recommendation`) to include new fields
- [x] Update scoring pipeline to pass through all location metadata
- [x] Add complete test suite for dataset expansion validation
- [x] Verify API responses include all enriched location data

### 3. Error Taxonomy & Mapping
- [x] Define `UpstreamError`, `TimeoutBudgetExceeded`, `LocationNotFound`
- [x] Exception handlers → `ErrorPayload` with status codes
- [x] Tests added for 502/404/504 error scenarios

### 4. Infrastructure Hardening
- [x] Fix logging middleware explosions (dedicated logger with JSON serialization)
- [x] Verify Mapbox geocoding integration with proper token handling
- [x] Establish PowerShell-native testing patterns for Windows development

### 5. OpenAPI Documentation Polish ✅
- [x] Add comprehensive field docstrings with units (miles, °F, %, ISO local hour)
- [x] Update endpoint descriptions to reflect expanded dataset capabilities
- [x] Add example responses showcasing category, elevation, state, timezone fields
- [x] Document conditional request behavior (If-None-Match → 304)
- [x] Add OpenAPI schema validation for new location metadata fields
- [x] Create comprehensive API documentation with examples and error scenarios
- [x] Add server configurations and contact information
- [x] Implement proper tagging and categorization for API endpoints

## In Progress 🟡

## Future Tasks (Phase B+)

### 6. Cache Unification
- [ ] Remove any Redis dependency paths; single cache impl

### 7. Security Lite
- [ ] CORS allowlist, headers; optional API key gate

## Dataset Expansion Details

**Before:** ~50 locations with basic lat/lon/name data
**After:** 100 locations with comprehensive metadata:

```json
{
  "id": 69,
  "name": "Deception Pass_69",
  "lat": 48.44522,
  "lon": -122.615167,
  "category": "Forest",           // NEW: Location classification
  "elevation": 0.0,               // NEW: Topographic context  
  "state": "WA",                  // NEW: Geographic organization
  "timezone": "America/Los_Angeles", // NEW: Local time calculations
  "distance_mi": 59.6,
  "score": 94.03,
  "sun_start_iso": "2025-08-23T08:00",
  "duration_hours": 10
}
```

**Categories Include:** Forest, Gorge, Beach, Lake, Mountain, Valley, etc.
**Geographic Coverage:** Washington, Oregon, Idaho (Pacific Northwest)
**Validation:** All tests passing, API responses verified

## Success Criteria ✅

- [x] 100% test coverage for dataset expansion
- [x] API responses include all new metadata fields
- [x] Backward compatibility maintained for existing clients
- [x] Performance impact negligible (all tests sub-second)
- [x] Documentation updated to reflect expanded capabilities

## Next Phase

**Phase B Status: ✅ COMPLETE**

All core Phase B production polish tasks have been successfully completed:
- ✅ Conditional Requests: Full ETag/If-None-Match implementation
- ✅ Dataset Expansion: 100 locations with comprehensive metadata  
- ✅ Error Handling: Complete taxonomy with proper HTTP status codes
- ✅ Infrastructure: Logging fixes, geocoding verification, testing patterns
- ✅ OpenAPI Documentation: Comprehensive API documentation with examples

**Next Phase Options:**
- **Phase C - Frontend Integration**: Mobile app development with Flutter
- **Phase D - Load Testing**: Performance optimization and scaling preparation  
- **Phase B+ - Advanced Hardening**: Cache unification and security enhancements
