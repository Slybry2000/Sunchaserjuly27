import 'package:flutter/services.dart';

/// Manages location images with fallback strategy:
/// 1. Specific location image (future)
/// 2. Category-based local asset
/// 3. Category-based external URL
/// 4. Default placeholder
class LocationImageService {
  
  /// Map of categories to local asset paths
  static const Map<String, String> _categoryAssets = {
    'forest': 'assets/images/categories/forest.jpg',
    'gorge': 'assets/images/categories/gorge.jpg', 
    'beach': 'assets/images/categories/beach.jpg',
    'lake': 'assets/images/categories/lake.jpg',
    'mountain': 'assets/images/categories/mountain.jpg',
    'valley': 'assets/images/categories/valley.jpg',
    'urban park': 'assets/images/categories/urban_park.jpg',
    'park': 'assets/images/categories/park.jpg',
    'island': 'assets/images/categories/island.jpg',
    'climbing': 'assets/images/categories/climbing.jpg',
    'trail': 'assets/images/categories/trail.jpg',
    'desert': 'assets/images/categories/desert.jpg',
  };

  /// Fallback external URLs for categories (current implementation)
  static const Map<String, String> _categoryUrls = {
    'forest': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=240&fit=crop&crop=center',
    'gorge': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=240&fit=crop&crop=center',
    'beach': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&h=240&fit=crop&crop=center',
    'lake': 'https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=400&h=240&fit=crop&crop=center',
    'mountain': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=240&fit=crop&crop=center',
    'valley': 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400&h=240&fit=crop&crop=center',
    'urban park': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=240&fit=crop&crop=center',
    'park': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=240&fit=crop&crop=center',
    'island': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=240&fit=crop&crop=center',
    'climbing': 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400&h=240&fit=crop&crop=center',
    'trail': 'https://images.unsplash.com/photo-1551632811-561732d1e306?w=400&h=240&fit=crop&crop=center',
    'desert': 'https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=400&h=240&fit=crop&crop=center',
  };

  /// Get the best available image URL for a location
  static String getLocationImageUrl(String locationId, String category) {
    // Future: Check for specific location images
    // if (hasSpecificImage(locationId)) return getSpecificImageUrl(locationId);
    
    // Try category-based local asset first
    final assetPath = getCategoryAssetPath(category);
    if (assetPath != null) {
      return assetPath;
    }
    
    // Fallback to external URL
    return getCategoryImageUrl(category);
  }

  /// Get local asset path for category (returns null if not available)
  static String? getCategoryAssetPath(String category) {
    final normalizedCategory = category.toLowerCase().trim();
    final assetPath = _categoryAssets[normalizedCategory];
    
    if (assetPath != null) {
      // TODO: Check if asset actually exists in the bundle
      // For now, assume external URLs until we add actual assets
      return null;
    }
    
    return null;
  }

  /// Get external URL for category (always available fallback)
  static String getCategoryImageUrl(String category) {
    final normalizedCategory = category.toLowerCase().trim();
    return _categoryUrls[normalizedCategory] ?? _categoryUrls['mountain']!;
  }

  /// Check if local asset exists (future implementation)
  static Future<bool> hasLocalAsset(String assetPath) async {
    try {
      await rootBundle.load(assetPath);
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Get placeholder asset path
  static String getPlaceholderPath() {
    return 'assets/placeholder.png';
  }

  /// List all required category assets for download/sourcing
  static List<CategoryImageSpec> getRequiredAssets() {
    return _categoryAssets.entries.map((entry) => CategoryImageSpec(
      category: entry.key,
      assetPath: entry.value,
      fallbackUrl: _categoryUrls[entry.key] ?? '',
      description: _getCategoryDescription(entry.key),
    )).toList();
  }

  static String _getCategoryDescription(String category) {
    switch (category.toLowerCase()) {
      case 'forest': return 'Dense woodland with hiking trails';
      case 'gorge': return 'River valley with dramatic cliffs';
      case 'beach': return 'Coastal area with ocean views';
      case 'lake': return 'Freshwater body with scenic shores';
      case 'mountain': return 'High-elevation peak with vistas';
      case 'valley': return 'Low-lying area with open landscapes';
      case 'urban park': return 'City park with recreational facilities';
      case 'park': return 'Natural park area with trails';
      case 'island': return 'Island location with water views';
      case 'climbing': return 'Rock climbing area with challenging routes';
      case 'trail': return 'Hiking trail through natural terrain';
      case 'desert': return 'Arid landscape with unique geology';
      default: return 'Beautiful outdoor location';
    }
  }
}

/// Specification for a category image asset
class CategoryImageSpec {
  final String category;
  final String assetPath;
  final String fallbackUrl;
  final String description;

  const CategoryImageSpec({
    required this.category,
    required this.assetPath,
    required this.fallbackUrl,
    required this.description,
  });

  @override
  String toString() => '$category: $assetPath (fallback: ${fallbackUrl.substring(0, 50)}...)';
}
