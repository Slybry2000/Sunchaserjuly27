import pytest
from utils.geo import haversine_miles, bbox_degrees
from services.locations import all_locations, nearby

def test_haversine_seattle_tacoma():
    # Seattle: 47.6062, -122.3321; Tacoma: 47.2529, -122.4443
    dist = haversine_miles(47.6062, -122.3321, 47.2529, -122.4443)
    assert 22 <= dist <= 26

def test_bbox_degrees():
    min_lat, min_lon, max_lat, max_lon = bbox_degrees(47.6, -122.3, 10)
    assert min_lat < 47.6 < max_lat
    assert min_lon < -122.3 < max_lon

def test_all_locations_loads():
    locs = all_locations()
    assert isinstance(locs, list)
    assert len(locs) >= 50

def test_nearby_radius_and_order():
    lat, lon = 47.6062, -122.3321
    results = nearby(lat, lon, 30, max_candidates=10)
    for r in results:
        assert r["distance_mi"] <= 30
    dists = [r["distance_mi"] for r in results]
    assert dists == sorted(dists)
    assert len(results) <= 10
