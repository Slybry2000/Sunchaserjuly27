from Backend.utils.geo import haversine, clamp_bbox, normalize_latlon

def test_haversine_known_distance():
    # Seattle (47.6062, -122.3321) to Portland (45.5152, -122.6784) ~233km
    dist = haversine(47.6062, -122.3321, 45.5152, -122.6784)
    assert 230 < dist < 240

def test_clamp_bbox():
    min_lat, min_lon, max_lat, max_lon = clamp_bbox(47.0, -122.0, 100)
    assert min_lat < 47.0 < max_lat
    assert min_lon < -122.0 < max_lon

def test_normalize_latlon():
    lat, lon = normalize_latlon(95, 200)
    assert lat == 90.0
    assert -180 <= lon <= 180
