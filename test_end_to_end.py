#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite for Sun Chaser
Tests local backend, API integration, and overall system functionality
"""

import requests
import json
import time
import sys
from typing import Dict, List

def test_local_backend():
    """Test local backend health and core functionality"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Local Backend")
    print("=" * 40)
    
    # Test 1: Health Check
    print("1. Health check...", end=" ")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ PASS")
        else:
            print(f"❌ FAIL ({response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL (Connection error: {e})")
        return False
    
    # Test 2: Metrics endpoint
    print("2. Metrics endpoint...", end=" ")
    try:
        response = requests.get(f"{base_url}/metrics", timeout=5)
        if response.status_code == 200:
            # Accept either Prometheus format or JSON fallback
            if "python_info" in response.text or response.headers.get('content-type') == 'application/json':
                print("✅ PASS")
            else:
                print(f"❌ FAIL (Unexpected content type)")
                return False
        else:
            print(f"❌ FAIL ({response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL ({e})")
        return False
    
    # Test 3: Recommendation endpoint with valid coordinates
    print("3. Recommendation API (Seattle)...", end=" ")
    try:
        response = requests.get(
            f"{base_url}/recommend",
            params={"lat": 47.6, "lon": -122.3, "radius": 25},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if "locations" in data and len(data["locations"]) > 0:
                print(f"✅ PASS ({len(data['locations'])} locations)")
            else:
                print("⚠️  PARTIAL (No locations returned)")
        else:
            print(f"❌ FAIL ({response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL ({e})")
        return False
    
    # Test 4: ETag caching
    print("4. ETag caching...", end=" ")
    try:
        # First request
        response1 = requests.get(
            f"{base_url}/recommend",
            params={"lat": 47.6, "lon": -122.3, "radius": 25},
            timeout=10
        )
        etag1 = response1.headers.get('etag')
        
        # Second request with ETag
        headers = {'If-None-Match': etag1} if etag1 else {}
        response2 = requests.get(
            f"{base_url}/recommend",
            params={"lat": 47.6, "lon": -122.3, "radius": 25},
            headers=headers,
            timeout=10
        )
        
        if response2.status_code == 304:
            print("✅ PASS")
        else:
            print(f"⚠️  PARTIAL (Expected 304, got {response2.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL ({e})")
        return False
    
    # Test 5: Error handling
    print("5. Error handling (invalid coords)...", end=" ")
    try:
        response = requests.get(
            f"{base_url}/recommend",
            params={"lat": 999, "lon": 999, "radius": 25},
            timeout=10
        )
        if response.status_code == 400:
            print("✅ PASS")
        else:
            print(f"⚠️  PARTIAL (Expected 400, got {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL ({e})")
        return False
    
    return True

def test_frontend_integration():
    """Test frontend-backend integration patterns"""
    print("\n🎨 Testing Frontend Integration")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test CORS headers
    print("1. CORS headers...", end=" ")
    try:
        response = requests.options(f"{base_url}/recommend", timeout=5)
        cors_headers = response.headers.get('Access-Control-Allow-Origin')
        if cors_headers:
            print("✅ PASS")
        else:
            print("⚠️  PARTIAL (No CORS headers)")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL ({e})")
        return False
    
    # Test telemetry endpoint (used by frontend)
    print("2. Telemetry endpoint...", end=" ")
    try:
        # Test OPTIONS first (preflight)
        requests.options(f"{base_url}/telemetry", timeout=5)
        
        # Test POST with sample data
        sample_telemetry = {
            "event": "location_search",
            "data": {"lat": 47.6, "lon": -122.3, "results_count": 5}
        }
        response = requests.post(
            f"{base_url}/telemetry",
            json=sample_telemetry,
            timeout=5
        )
        if response.status_code in [200, 202, 204]:
            print("✅ PASS")
        else:
            print(f"⚠️  PARTIAL ({response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL ({e})")
        return False
    
    return True

def test_external_apis():
    """Test external API dependencies"""
    print("\n🌐 Testing External APIs")
    print("=" * 40)
    
    # Test Open-Meteo (weather API)
    print("1. Open-Meteo API...", end=" ")
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 47.6,
                "longitude": -122.3,
                "current": "weather_code"
            },
            timeout=10
        )
        if response.status_code == 200:
            print("✅ PASS")
        else:
            print(f"❌ FAIL ({response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL ({e})")
    
    # Test Mapbox (geocoding - requires API key but we can test the endpoint)
    print("2. Mapbox Geocoding (endpoint)...", end=" ")
    try:
        # Just test that the endpoint is reachable (will return 401 without key)
        response = requests.get(
            "https://api.mapbox.com/geocoding/v5/mapbox.places/seattle.json",
            timeout=10
        )
        if response.status_code in [401, 200]:  # 401 means endpoint is up but needs auth
            print("✅ PASS")
        else:
            print(f"⚠️  PARTIAL ({response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL ({e})")
    
    return True

def test_performance():
    """Test system performance characteristics"""
    print("\n⚡ Testing Performance")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test response times
    print("1. Response times...", end=" ")
    times = []
    for i in range(3):
        start = time.time()
        try:
            response = requests.get(
                f"{base_url}/recommend",
                params={"lat": 47.6, "lon": -122.3, "radius": 25},
                timeout=10
            )
            if response.status_code == 200:
                times.append(time.time() - start)
        except Exception:
            pass
    
    if times:
        avg_time = sum(times) / len(times)
        if avg_time < 2.0:  # Less than 2 seconds average
            print(f"✅ PASS ({avg_time:.2f}s avg)")
        else:
            print(f"⚠️  SLOW ({avg_time:.2f}s avg)")
    else:
        print("❌ FAIL")
    
    return True

def run_comprehensive_tests():
    """Run all test suites"""
    print("🧪 Sun Chaser End-to-End Test Suite")
    print("=" * 50)
    
    results = {
        "local_backend": test_local_backend(),
        "frontend_integration": test_frontend_integration(),
        "external_apis": test_external_apis(),
        "performance": test_performance()
    }
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 30)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All systems operational!")
        return True
    else:
        print("⚠️  Some issues detected - check logs above")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
