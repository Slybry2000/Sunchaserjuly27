"""
Tests for expanded dataset functionality with category column
"""
from Backend.services.locations import all_locations, nearby


def test_dataset_size_and_schema():
    """Test that dataset has ≥100 locations with all required columns"""
    locations = all_locations()
    
    # Verify size requirement
    assert len(locations) >= 100, f"Dataset should have ≥100 locations, got {len(locations)}"
    
    # Verify schema
    required_fields = ['id', 'name', 'lat', 'lon', 'elevation', 'category', 'state', 'timezone']
    for field in required_fields:
        assert field in locations[0], f"Missing required field: {field}"
    
    # Verify data types
    assert isinstance(locations[0]['lat'], float)
    assert isinstance(locations[0]['lon'], float) 
    assert isinstance(locations[0]['elevation'], float)
    assert isinstance(locations[0]['category'], str)
    assert isinstance(locations[0]['state'], str)


def test_category_diversity():
    """Test that dataset has diverse categories"""
    locations = all_locations()
    categories = set(loc['category'] for loc in locations)
    
    # Should have multiple categories
    assert len(categories) >= 5, f"Should have ≥5 categories, got {len(categories)}: {categories}"
    
    # Check for expected categories
    expected_categories = {'Mountain', 'Lake', 'Park', 'Beach', 'Forest'}
    found_categories = categories.intersection(expected_categories)
    assert len(found_categories) >= 3, f"Should have common categories, found: {found_categories}"


def test_nearby_includes_category():
    """Test that nearby search results include category information"""
    # Search around Seattle area
    results = nearby(47.6, -122.3, 100, max_candidates=10)
    
    assert len(results) > 0, "Should find nearby locations"
    
    # Verify all results have category
    for result in results:
        assert 'category' in result, "Nearby results should include category"
        assert isinstance(result['category'], str), "Category should be string"
        assert len(result['category']) > 0, "Category should not be empty"


def test_geographic_coverage():
    """Test that dataset covers both WA and OR states"""
    locations = all_locations()
    states = set(loc['state'] for loc in locations)
    
    # Should cover both states
    assert 'WA' in states, "Dataset should include Washington locations"
    assert 'OR' in states, "Dataset should include Oregon locations" 
    
    # Should have reasonable distribution
    wa_count = sum(1 for loc in locations if loc['state'] == 'WA')
    or_count = sum(1 for loc in locations if loc['state'] == 'OR')
    
    assert wa_count > 10, f"Should have >10 WA locations, got {wa_count}"
    assert or_count > 10, f"Should have >10 OR locations, got {or_count}"


def test_elevation_data():
    """Test that elevation data is present and reasonable"""
    locations = all_locations()
    
    elevations = [loc['elevation'] for loc in locations]
    
    # Should have variety in elevations
    min_elev = min(elevations)
    max_elev = max(elevations)
    
    assert min_elev >= 0, f"Minimum elevation should be ≥0, got {min_elev}"
    assert max_elev > 1000, f"Should have high elevation locations, max: {max_elev}"
    assert max_elev - min_elev > 2000, f"Should have elevation variety, range: {max_elev - min_elev}"
