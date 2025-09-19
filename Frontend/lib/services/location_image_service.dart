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

  /// Fallback external URL pools for categories (multiple choices -> variety)
  /// These are representative Unsplash photo IDs (public hotlink format). All
  /// remain hotlinked (no local caching beyond browser rules). We choose one
  /// deterministically per location to avoid every card sharing the same image.
  // Pools now contain map entries with both the hotlink URL and an optional
  // Unsplash API id (apiId). When apiId is present the frontend will pass it
  // to the backend so the backend can fetch real attribution.
  static const Map<String, List<dynamic>> _categoryUrlPools = {
    'forest': [
      // jNmXsyp1Bl0: tall trees; Lu8AoWCXATg: misty blue foothills
      {'url': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=240&fit=crop&crop=center', 'apiId': 'jNmXsyp1Bl0'},
      {'url': 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=400&h=240&fit=crop&crop=center', 'apiId': 'Lu8AoWCXATg'},
    ],
    'gorge': [
      // zIye2BBW6DU: waterfall in forest (Gorge vibe)
      {'url': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=240&fit=crop&crop=center', 'apiId': 'zIye2BBW6DU'},
    ],
    'beach': [
      // wb2UdxVof_g: Oregon coast sea stacks
      {'url': 'https://images.unsplash.com/photo-1506617420156-8e4536971650?w=400&h=240&fit=crop&crop=center', 'apiId': 'wb2UdxVof_g'},
    ],
    'lake': [
      // OV7iMdaAJTg: Lake Washington waves; J5B1NDtaH50/67oRvO9Z57s: Crater Lake views
      {'url': 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400&h=240&fit=crop&crop=center', 'apiId': 'OV7iMdaAJTg'},
      {'url': 'https://images.unsplash.com/photo-1500042002066-611b1c1ffbb7?w=400&h=240&fit=crop&crop=center', 'apiId': 'J5B1NDtaH50'},
      {'url': 'https://images.unsplash.com/photo-1516478177764-9fe5bd7e971f?w=400&h=240&fit=crop&crop=center', 'apiId': '67oRvO9Z57s'},
    ],
    'mountain': [
      // Re-iyBoo8aQ: Mt Hood at Trillium Lake (classic)
      {'url': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=240&fit=crop&crop=center', 'apiId': 'Re-iyBoo8aQ'},
      {'url': 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=400&h=240&fit=crop&crop=center', 'apiId': 'Lu8AoWCXATg'},
    ],
    'valley': [
      {'url': 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=400&h=240&fit=crop&crop=center', 'apiId': 'Lu8AoWCXATg'},
    ],
    'urban park': [
      {'url': 'https://images.unsplash.com/photo-1526414060640-7fd91fc51bf2?w=400&h=240&fit=crop&crop=center', 'apiId': 'GCo3fo6UZ1U'},
      {'url': 'https://images.unsplash.com/photo-1532465611-5a99c98e9ca2?w=400&h=240&fit=crop&crop=center', 'apiId': 'HFJ65-zt5s4'},
    ],
    'park': [
      {'url': 'https://images.unsplash.com/photo-1526414060640-7fd91fc51bf2?w=400&h=240&fit=crop&crop=center', 'apiId': 'GCo3fo6UZ1U'},
      {'url': 'https://images.unsplash.com/photo-1532465611-5a99c98e9ca2?w=400&h=240&fit=crop&crop=center', 'apiId': 'HFJ65-zt5s4'},
    ],
    'island': [
      {'url': 'https://images.unsplash.com/photo-1565183406115-15b63f5f2f9f?w=400&h=240&fit=crop&crop=center', 'apiId': 'TGKHFFHRM80'},
    ],
    'climbing': [
      {'url': 'https://images.unsplash.com/photo-1525865926350-7b6a08053cea?w=400&h=240&fit=crop&crop=center', 'apiId': 'ojjc5uA4lCI'},
      {'url': 'https://images.unsplash.com/photo-1567976922229-b7bdbd1b3b54?w=400&h=240&fit=crop&crop=center', 'apiId': 'oMjnWW5vjRI'},
    ],
    'trail': [
      {'url': 'https://images.unsplash.com/photo-1499084732479-de2c02d45fc4?w=400&h=240&fit=crop&crop=center', 'apiId': 'PSYVXvAitAQ'},
    ],
    'desert': [
      {'url': 'https://images.unsplash.com/photo-1496024840928-4c417adf211d?w=400&h=240&fit=crop&crop=center', 'apiId': '1v__2MdOPWU'},
    ],
  };

  /// Get the best available image URL for a location
  /// Returns the image URL for a location (chooses by seed). If the chosen
  /// pool entry contains an `apiId` the caller can request attribution with it.
  static String getLocationImageUrl(String locationId, String category) {
    // Future: Check for specific location images
    // if (hasSpecificImage(locationId)) return getSpecificImageUrl(locationId);
    
    // Try category-based local asset first
    final assetPath = getCategoryAssetPath(category);
    if (assetPath != null) {
      return assetPath;
    }
    
    // Fallback to external URL
  return getCategoryImageUrl(category, seed: locationId)['url'] as String;
  }

  /// Async variant of `getLocationImageUrl` which checks the asset bundle
  /// to ensure a local asset actually exists before returning it. This is
  /// non-breaking: the synchronous `getLocationImageUrl` remains available
  /// for callers that don't need an existence guarantee.
  static Future<String> getLocationImageUrlAsync(String locationId, String category) async {
    // Prefer verified local asset if present
    final local = await getCategoryAssetPathAsync(category);
    if (local != null) return local;

    // Fallback to external URL
    final entry = getCategoryImageUrl(category, seed: locationId);
    return entry['url'] ?? '';
  }

  /// Get local asset path for category (returns null if not available)
  static String? getCategoryAssetPath(String category) {
    final normalizedCategory = category.toLowerCase().trim();
    final assetPath = _categoryAssets[normalizedCategory];
    
    if (assetPath != null) {
      // Note: verifying the asset actually exists at runtime requires an
      // asynchronous asset bundle check (e.g. `rootBundle.load`). To avoid
      // changing this synchronous API, callers that need a guaranteed-valid
      // asset path should use `getCategoryAssetPathAsync(category)` below.
      // For compatibility, return the configured asset path here (may be
      // absent in some test/CI environments), callers may prefer the async
      // check to confirm presence.
      return assetPath;
    }
    
    return null;
  }

  /// Async variant that checks the asset bundle to confirm the asset exists.
  /// Returns the asset path if present, otherwise null.
  static Future<String?> getCategoryAssetPathAsync(String category) async {
    final normalizedCategory = category.toLowerCase().trim();
    final assetPath = _categoryAssets[normalizedCategory];
    if (assetPath == null) return null;
    try {
      await rootBundle.load(assetPath);
      return assetPath;
    } catch (_) {
      return null;
    }
  }

  /// Get external URL for category (always available fallback)
  /// Select an external URL for a category. If a seed (e.g., locationId) is
  /// provided we choose deterministically so the same location gets the same
  /// photo across rebuilds while different locations in the same category can
  /// show different photos for visual variety.
  /// Return the chosen pool entry as a map with `url` and optional `apiId`.
  static Map<String, String> getCategoryImageUrl(String category, {String? seed}) {
    final normalizedCategory = category.toLowerCase().trim();
    final pool = _categoryUrlPools[normalizedCategory] ?? _categoryUrlPools['mountain']!;
    int idx = 0;
    if (pool.length > 1 && seed != null && seed.isNotEmpty) {
      final hash = seed.codeUnits.fold<int>(0, (a, c) => (a * 31 + c) & 0x7fffffff);
      idx = hash % pool.length;
    }
    final entry = pool[idx];
    if (entry is Map<String, String>) return entry;
    if (entry is String) return {'url': entry, 'apiId': ''};
    // Fallback defensive
    return {'url': entry.toString(), 'apiId': ''};
  }

  /// Return the entire pool (first element is canonical primary) for fallback logic.
  /// Return the entire pool of map entries (url + apiId)
  static List<Map<String, String>> getCategoryImagePool(String category) {
    final normalizedCategory = category.toLowerCase().trim();
    final raw = _categoryUrlPools[normalizedCategory] ?? _categoryUrlPools['mountain']!;
    return raw.map<Map<String, String>>((entry) {
      if (entry is Map<String, String>) return entry;
      if (entry is String) return {'url': entry, 'apiId': ''};
      return {'url': entry.toString(), 'apiId': ''};
    }).toList(growable: false);
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
    return _categoryAssets.entries.map((entry) {
      final pool = _categoryUrlPools[entry.key];
      String fallback = '';
      if (pool != null && pool.isNotEmpty) {
        final first = pool.first;
        if (first is Map<String, String>) {
          fallback = first['url'] ?? '';
        } else if (first is String) {
          fallback = first;
        }
      }
      return CategoryImageSpec(
        category: entry.key,
        assetPath: entry.value,
        fallbackUrl: fallback,
        description: _getCategoryDescription(entry.key),
      );
    }).toList();
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
