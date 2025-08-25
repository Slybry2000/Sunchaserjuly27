# OpenAPI Documentation Examples

This file contains example responses for the Sunshine Backend API to showcase
the comprehensive location metadata and various response scenarios.

## Example 1: Successful Recommendation Response

```json
{
  "query": {
    "lat": 47.603243,
    "lon": -122.330286,
    "radius": 100
  },
  "results": [
    {
      "id": "69",
      "name": "Deception Pass_69",
      "lat": 48.44522,
      "lon": -122.615167,
      "elevation": 0.0,
      "category": "Forest",
      "state": "WA",
      "timezone": "America/Los_Angeles",
      "distance_mi": 59.6,
      "sun_start_iso": "2024-12-30T10:00",
      "duration_hours": 6,
      "score": 94.03
    },
    {
      "id": "84",
      "name": "Crater Lake Rim_84",
      "lat": 42.9446,
      "lon": -122.1090,
      "elevation": 7100.0,
      "category": "Lake",
      "state": "OR",
      "timezone": "America/Los_Angeles",
      "distance_mi": 285.2,
      "sun_start_iso": "2024-12-30T09:30",
      "duration_hours": 8,
      "score": 87.45
    },
    {
      "id": "23",
      "name": "Columbia River Gorge_23",
      "lat": 45.7312,
      "lon": -121.7113,
      "elevation": 200.0,
      "category": "Gorge",
      "state": "WA",
      "timezone": "America/Los_Angeles", 
      "distance_mi": 174.8,
      "sun_start_iso": "2024-12-30T11:00",
      "duration_hours": 5,
      "score": 82.91
    }
  ],
  "generated_at": "2024-12-30T18:00:00Z",
  "version": "v1"
}
```

## Example 2: Location Categories

Our dataset includes diverse location categories:

- **Forest**: Dense woodland areas perfect for hiking and nature photography
- **Gorge**: Dramatic river valleys with scenic overlooks and waterfalls
- **Beach**: Coastal areas with ocean views and sandy shores
- **Lake**: Freshwater bodies ideal for water activities and reflective scenery
- **Mountain**: High-elevation peaks with panoramic views
- **Valley**: Low-lying areas with agricultural or pastoral landscapes

## Example 3: Error Response Examples

### 400 Bad Request - Geocoding Disabled
```json
{
  "error": "geocoding_disabled",
  "detail": "Query (?q=) is disabled; provide lat/lon or set ENABLE_Q=true.",
  "hint": "Use ?lat=..&lon=.."
}
```

### 422 Unprocessable Entity - Missing Coordinates
```json
{
  "error": "missing_coords", 
  "detail": "lat and lon are required.",
  "hint": "Example: /recommend?lat=47.6&lon=-122.3"
}
```

### 502 Bad Gateway - Weather Service Unavailable
```json
{
  "error": "weather_unavailable",
  "detail": "Weather service unavailable",
  "hint": "Try again later"
}
```

## Example 4: Geocoding Response

```json
{
  "query": "Seattle, WA",
  "lat": 47.603243,
  "lon": -122.330286,
  "address": "Seattle, Washington, United States"
}
```

## Example 5: Health Check Response

```json
{
  "status": "ok"
}
```

## Example 6: Conditional Request Headers

### Request with ETag
```
GET /recommend?lat=47.6&lon=-122.3&radius=50
If-None-Match: "abc123def456"
```

### 304 Not Modified Response
```
HTTP/1.1 304 Not Modified
ETag: "abc123def456"
Cache-Control: public, max-age=900, stale-while-revalidate=300
Last-Modified: Mon, 30 Dec 2024 18:00:00 GMT
```

## Example 7: Comprehensive Location Metadata

Each location in our dataset includes:

```json
{
  "id": "42",
  "name": "Mount Rainier Paradise_42",
  "lat": 46.7869,
  "lon": -121.7359,
  "elevation": 5400.0,           // Elevation in feet above sea level
  "category": "Mountain",        // Activity-based categorization
  "state": "WA",                 // US state for geographic organization
  "timezone": "America/Los_Angeles", // IANA timezone for local time calculations
  "distance_mi": 87.3,           // Distance from query origin (1 decimal)
  "sun_start_iso": "2024-12-30T08:45", // Local time when sunshine begins
  "duration_hours": 7,           // Expected sunshine duration in hours
  "score": 91.26                 // Recommendation score (2 decimals, 0-100)
}
```

This rich metadata enables frontend applications to provide:
- Activity-specific filtering by location category
- Elevation context for difficulty assessment
- Accurate local time displays using timezone information
- State-based geographic organization and routing
- Precise distance calculations for trip planning
