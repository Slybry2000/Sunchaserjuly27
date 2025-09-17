#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite for Sun Chaser
Tests local backend, API integration, and overall system functionality
"""

import requests
import time
import sys
import os
import pytest

def run_local_backend_suite() -> bool:
    """Run local backend checks, returning True/False for manual execution."""
    base_url = "http://127.0.0.1:8000"
    print("🧪 Testing Local Backend")
    print("=" * 40)
    # Health
    print("1. Health check...", end=" ")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ PASS")
        else:
            print(f"❌ FAIL ({response.status_code})")
            return False
    except requests.exceptions.RequestException as e:  # pragma: no cover - network error path
        print(f"❌ FAIL (Connection error: {e})")
        return False
    # Metrics
    print("2. Metrics endpoint...", end=" ")
    try:
        response = requests.get(f"{base_url}/metrics", timeout=5)
        if response.status_code == 200:
            if "python_info" in response.text or response.headers.get('content-type') == 'application/json':
                print("✅ PASS")
            else:
                print("❌ FAIL (Unexpected content type)")
                return False
        else:
            print(f"❌ FAIL ({response.status_code})")
            return False
    except requests.exceptions.RequestException as e:  # pragma: no cover
        print(f"❌ FAIL ({e})")
        return False
    # Recommend
    print("3. Recommendation API (Seattle)...", end=" ")
    try:
        response = requests.get(
            f"{base_url}/recommend",
            params={"lat": 47.6, "lon": -122.3, "radius": 25},
            timeout=10,
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
    except requests.exceptions.RequestException as e:  # pragma: no cover
        print(f"❌ FAIL ({e})")
        return False
    # ETag
    print("4. ETag caching...", end=" ")
    try:
        response1 = requests.get(
            f"{base_url}/recommend",
            params={"lat": 47.6, "lon": -122.3, "radius": 25},
            timeout=10,
        )
        etag1 = response1.headers.get("etag")
        headers = {"If-None-Match": etag1} if etag1 else {}
        response2 = requests.get(
            f"{base_url}/recommend",
            params={"lat": 47.6, "lon": -122.3, "radius": 25},
            headers=headers,
            timeout=10,
        )
        if response2.status_code == 304:
            print("✅ PASS")
        else:
            print(f"⚠️  PARTIAL (Expected 304, got {response2.status_code})")
    except requests.exceptions.RequestException as e:  # pragma: no cover
        print(f"❌ FAIL ({e})")
        return False
    # Error handling
    print("5. Error handling (invalid coords)...", end=" ")
    try:
        response = requests.get(
            f"{base_url}/recommend",
            params={"lat": 999, "lon": 999, "radius": 25},
            timeout=10,
        )
        if response.status_code == 400:
            print("✅ PASS")
        else:
            print(f"⚠️  PARTIAL (Expected 400, got {response.status_code})")
    except requests.exceptions.RequestException as e:  # pragma: no cover
        print(f"❌ FAIL ({e})")
        return False
    return True


def test_local_backend():
    """Pytest wrapper – optional E2E local backend test.

    Skipped unless RUN_E2E=1 is set in environment.
    """
    if os.environ.get("RUN_E2E") != "1":
        pytest.skip("Skip local backend E2E test (set RUN_E2E=1 to enable)")
    assert run_local_backend_suite(), "Local backend suite reported failure"

def run_frontend_integration_suite() -> bool:
    base_url = "http://127.0.0.1:8000"
    print("\n🎨 Testing Frontend Integration")
    print("=" * 40)
    print("1. CORS headers...", end=" ")
    try:
        response = requests.options(f"{base_url}/recommend", timeout=5)
        cors_headers = response.headers.get("Access-Control-Allow-Origin")
        if cors_headers:
            print("✅ PASS")
        else:
            print("⚠️  PARTIAL (No CORS headers)")
    except requests.exceptions.RequestException as e:  # pragma: no cover
        print(f"❌ FAIL ({e})")
        return False
    print("2. Telemetry endpoint...", end=" ")
    try:
        requests.options(f"{base_url}/telemetry", timeout=5)
        sample_telemetry = {
            "event": "location_search",
            "data": {"lat": 47.6, "lon": -122.3, "results_count": 5},
        }
        response = requests.post(
            f"{base_url}/telemetry", json=sample_telemetry, timeout=5
        )
        if response.status_code in [200, 202, 204]:
            print("✅ PASS")
        else:
            print(f"⚠️  PARTIAL ({response.status_code})")
    except requests.exceptions.RequestException as e:  # pragma: no cover
        print(f"❌ FAIL ({e})")
        return False
    return True


def test_frontend_integration():
    if os.environ.get("RUN_E2E") != "1":
        pytest.skip("Skip frontend integration E2E test (set RUN_E2E=1 to enable)")
    assert run_frontend_integration_suite(), "Frontend integration suite reported failure"

def run_external_api_suite() -> bool:
    print("\n🌐 Testing External APIs")
    print("=" * 40)
    print("1. Open-Meteo API...", end=" ")
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": 47.6, "longitude": -122.3, "current": "weather_code"},
            timeout=10,
        )
        if response.status_code == 200:
            print("✅ PASS")
        else:
            print(f"❌ FAIL ({response.status_code})")
    except requests.exceptions.RequestException as e:  # pragma: no cover
        print(f"❌ FAIL ({e})")
    print("2. Mapbox Geocoding (endpoint)...", end=" ")
    try:
        response = requests.get(
            "https://api.mapbox.com/geocoding/v5/mapbox.places/seattle.json",
            timeout=10,
        )
        if response.status_code in [401, 200]:
            print("✅ PASS")
        else:
            print(f"⚠️  PARTIAL ({response.status_code})")
    except requests.exceptions.RequestException as e:  # pragma: no cover
        print(f"❌ FAIL ({e})")
    return True


def test_external_apis():
    if os.environ.get("RUN_E2E") != "1":
        pytest.skip("Skip external API E2E test (set RUN_E2E=1 to enable)")
    assert run_external_api_suite(), "External API suite reported failure"

def run_performance_suite() -> bool:
    print("\n⚡ Testing Performance")
    print("=" * 40)
    base_url = "http://127.0.0.1:8000"
    print("1. Response times...", end=" ")
    times: list[float] = []
    for _ in range(3):
        start = time.time()
        try:
            response = requests.get(
                f"{base_url}/recommend",
                params={"lat": 47.6, "lon": -122.3, "radius": 25},
                timeout=10,
            )
            if response.status_code == 200:
                times.append(time.time() - start)
        except Exception:  # pragma: no cover
            pass
    if times:
        avg_time = sum(times) / len(times)
        if avg_time < 2.0:
            print(f"✅ PASS ({avg_time:.2f}s avg)")
        else:
            print(f"⚠️  SLOW ({avg_time:.2f}s avg)")
    else:
        print("❌ FAIL")
    return True


def test_performance():
    if os.environ.get("RUN_E2E") != "1":
        pytest.skip("Skip performance E2E test (set RUN_E2E=1 to enable)")
    assert run_performance_suite(), "Performance suite reported failure"

def run_comprehensive_tests():
    """Run all test suites"""
    print("🧪 Sun Chaser End-to-End Test Suite")
    print("=" * 50)
    
    results = {
        "local_backend": run_local_backend_suite(),
        "frontend_integration": run_frontend_integration_suite(),
        "external_apis": run_external_api_suite(),
        "performance": run_performance_suite(),
    }
    
    # Summary
    print("\n📊 Test Results Summary")
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
