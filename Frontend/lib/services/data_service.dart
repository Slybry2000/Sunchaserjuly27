import 'dart:convert';
import 'dart:math';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:sunshine_spotter/services/api_client.dart';
import 'package:sunshine_spotter/services/telemetry_service.dart';
import 'package:sunshine_spotter/services/location_image_service.dart';
import 'package:sunshine_spotter/config.dart';

class DataService {
  static const String _favoritesKey = 'favorites';

  // API base URL can be provided at build/run time via --dart-define=API_BASE_URL
  // Default uses Android emulator host mapping for local dev.
  static final ApiClient _apiClient = ApiClient(
    // Use helper so local web dev defaults to localhost.
    baseUrl: apiBaseUrl(),
  );

  // Sample spots now use category fallback Unsplash images instead of
  // brittle direct Pixabay image URLs returning 400 in web contexts.
  static final List<SunshineSpot> _sampleSpots = [
    SunshineSpot(
      id: '1',
      name: 'Sunny Beach Park',
      description: 'Beautiful beachfront park with golden sand and crystal clear waters. Perfect for sunbathing and beach volleyball.',
      latitude: 37.7749,
      longitude: -122.4194,
  imageUrl: LocationImageService.getCategoryImageUrl('beach')['url'] ?? '',
      sunshineHours: 8,
      temperature: 78.5,
      weather: 'Sunny',
      rating: 4.8,
      category: 'Beach',
      distance: 0,
    ),
    SunshineSpot(
      id: '2',
      name: 'Mountain Vista',
      description: 'Stunning mountain overlook with panoramic views and excellent hiking trails. Breathtaking sunrise and sunset views.',
      latitude: 37.8044,
      longitude: -122.2712,
  imageUrl: LocationImageService.getCategoryImageUrl('mountain')['url'] ?? '',
      sunshineHours: 7,
      temperature: 72.0,
      weather: 'Partly Cloudy',
      rating: 4.6,
      category: 'Mountain',
      distance: 0,
    ),
    SunshineSpot(
      id: '3',
      name: 'Riverside Gardens',
      description: 'Peaceful riverside park with walking paths, picnic areas, and beautiful flower gardens.',
      latitude: 37.7849,
      longitude: -122.4094,
  imageUrl: LocationImageService.getCategoryImageUrl('park')['url'] ?? '',
      sunshineHours: 6,
      temperature: 75.2,
      weather: 'Sunny',
      rating: 4.3,
      category: 'Park',
      distance: 0,
    ),
    SunshineSpot(
      id: '4',
      name: 'Wildflower Meadow',
      description: 'Open meadow filled with seasonal wildflowers and perfect for photography and relaxation.',
      latitude: 37.7649,
      longitude: -122.4394,
  imageUrl: LocationImageService.getCategoryImageUrl('valley')['url'] ?? '',
      sunshineHours: 9,
      temperature: 80.1,
      weather: 'Clear',
      rating: 4.9,
      category: 'Nature',
      distance: 0,
    ),
    SunshineSpot(
      id: '5',
      name: 'Lighthouse Point',
      description: 'Historic lighthouse with coastal views and dramatic cliff formations.',
      latitude: 37.8149,
      longitude: -122.4794,
  imageUrl: LocationImageService.getCategoryImageUrl('beach')['url'] ?? '',
      sunshineHours: 7,
      temperature: 74.8,
      weather: 'Sunny',
      rating: 4.5,
      category: 'Coast',
      distance: 0,
    ),
  ];

  static Future<List<SunshineSpot>> searchSpots({
    required double latitude,
    required double longitude,
    required double radiusMiles,
    String? q,
  }) async {
    final stopwatch = Stopwatch()..start();
    
    // Try backend API first (supports ETag revalidation). On any error, fall back
    // to the local sample generator so the UI still works offline/dev.
    try {
  final resp = await _apiClient.recommend(latitude, longitude, radius: radiusMiles.toInt(), q: q);
      if (resp != null) {
        // Map RecommendResponse -> SunshineSpot, ensuring per-category unique images
        final Map<String, Set<String>> usedUrlsByCategory = {};
        List<SunshineSpot> spots = resp.results.map((r) {
          final distance = _calculateDistance(latitude, longitude, r.lat, r.lon);
          final category = r.category;
          final pool = LocationImageService.getCategoryImagePool(category);
          // Choose an image URL:
          // - If backend provided photoId and it matches a pool apiId, use that pool URL.
          // - Else use deterministic category URL seeded by location id.
          String imageUrl;
          final pid = (r.photoId ?? '').trim();
          if (pid.isNotEmpty) {
            final match = pool.firstWhere(
              (e) => (e['apiId'] ?? '') == pid,
              orElse: () => const <String, String>{},
            );
            imageUrl = (match['url'] ?? '')
                .toString()
                .isNotEmpty
                ? match['url']!
                : LocationImageService.getCategoryImageUrl(category, seed: r.id)['url']!;
          } else {
            imageUrl = LocationImageService.getCategoryImageUrl(category, seed: r.id)['url']!;
          }

          // Enforce uniqueness per category within this response when possible
          final used = usedUrlsByCategory.putIfAbsent(category.toLowerCase(), () => <String>{});
          if (used.contains(imageUrl)) {
            // Try to find an alternative in the pool
            final alt = pool.firstWhere(
              (e) => !used.contains(e['url'] ?? ''),
              orElse: () => <String, String>{'url': imageUrl},
            );
            imageUrl = alt['url'] ?? imageUrl;
          }
          used.add(imageUrl);

          return SunshineSpot(
            id: r.id,
            name: r.name,
            description: _buildDescription(r),
            latitude: r.lat,
            longitude: r.lon,
            imageUrl: imageUrl,
            apiPhotoId: (r.photoId ?? '').isNotEmpty ? r.photoId : null,
            sunshineHours: r.durationHours,
            temperature: 70.0, // Could be enhanced with weather API temperature
            weather: 'Sunny',
            rating: (r.score / 100.0 * 5.0), // Convert 0-100 score to 0-5 rating
            category: category, // Use backend category
            distance: distance,
          );
        }).where((s) => s.distance <= radiusMiles).toList();

        // Sort by distance
        spots.sort((a, b) => a.distance.compareTo(b.distance));

        // Merge favorite status
        final favorites = await getFavorites();
        for (int i = 0; i < spots.length; i++) {
          spots[i] = spots[i].copyWith(
            isFavorite: favorites.any((fav) => fav.id == spots[i].id),
          );
        }

        stopwatch.stop();
        if (q != null && q.trim().isNotEmpty) {
          TelemetryService.logEvent('search', properties: {
            'q': q.trim(),
            'results_count': spots.length,
            'search_duration_ms': stopwatch.elapsedMilliseconds,
          });
        } else {
          TelemetryService.logSearch(
            latitude: latitude,
            longitude: longitude,
            radius: radiusMiles,
            resultsCount: spots.length,
            searchDuration: stopwatch.elapsed,
          );
        }

        return spots;
      }
    } catch (e) {
      TelemetryService.logError('Backend search failed', context: 'searchSpots', exception: e);
      
      // Instead of showing fake data, rethrow the error so the UI can show proper error state
      throw Exception('Unable to connect to service. Please check your internet connection and try again.');
    }

    // This fallback code is now unreachable - keeping for reference but should be removed
  // TODO-3: Remove this entire fallback section in next cleanup (see docs/INLINE_TODO_ISSUES.md)
    await Future.delayed(const Duration(milliseconds: 800));
    final Random random = Random();
    
    // Create random spots within the radius
    List<SunshineSpot> spots = _sampleSpots.map((spot) {
      // Generate random location within radius
      double lat = latitude + (random.nextDouble() - 0.5) * (radiusMiles / 69.0) * 2;
      double lng = longitude + (random.nextDouble() - 0.5) * (radiusMiles / 55.0) * 2;
      
      // Calculate distance from user location
      double distance = _calculateDistance(latitude, longitude, lat, lng);
      
      return spot.copyWith(
        latitude: lat,
        longitude: lng,
        distance: distance,
        temperature: 65 + random.nextDouble() * 25, // Random temp between 65-90°F
        sunshineHours: 5 + random.nextInt(6), // Random sunshine hours 5-10
      );
    }).where((spot) => spot.distance <= radiusMiles).toList();
    
    // Sort by distance
    spots.sort((a, b) => a.distance.compareTo(b.distance));
    
    // Add favorite status from local storage
    final favorites = await getFavorites();
    for (int i = 0; i < spots.length; i++) {
      spots[i] = spots[i].copyWith(
        isFavorite: favorites.any((fav) => fav.id == spots[i].id),
      );
    }
    
    return spots;
  }

  static double _calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    const double earthRadius = 3958.8; // Earth's radius in miles
    double lat1Rad = lat1 * (pi / 180);
    double lon1Rad = lon1 * (pi / 180);
    double lat2Rad = lat2 * (pi / 180);
    double lon2Rad = lon2 * (pi / 180);

    double deltaLat = lat2Rad - lat1Rad;
    double deltaLon = lon2Rad - lon1Rad;

    double a = sin(deltaLat / 2) * sin(deltaLat / 2) +
        cos(lat1Rad) * cos(lat2Rad) * sin(deltaLon / 2) * sin(deltaLon / 2);
    double c = 2 * atan2(sqrt(a), sqrt(1 - a));

    return earthRadius * c;
  }

  static String _buildDescription(dynamic recommendation) {
    final category = recommendation.category ?? 'Location';
    final state = recommendation.state ?? '';
    final elevation = recommendation.elevation ?? 0.0;
    
    String description = '';
    
    // Category-based description
    switch (category.toLowerCase()) {
      case 'forest':
        description = 'Dense woodland area perfect for hiking and nature photography';
        break;
      case 'gorge':
        description = 'Dramatic river valley with scenic overlooks and waterfalls';
        break;
      case 'beach':
        description = 'Coastal area with ocean views and sandy shores';
        break;
      case 'lake':
        description = 'Freshwater body ideal for water activities and reflective scenery';
        break;
      case 'mountain':
        description = 'High-elevation peak with panoramic views';
        break;
      case 'valley':
        description = 'Low-lying area with agricultural or pastoral landscapes';
        break;
      default:
        description = 'Beautiful outdoor location perfect for sunshine activities';
    }
    
    // Add elevation context if significant
    if (elevation > 1000) {
      description += ' at ${elevation.toInt()} feet elevation';
    }
    
    // Add state information
    if (state.isNotEmpty) {
      description += ' in $state';
    }
    
    return '$description.';
  }

  static Future<List<SunshineSpot>> getFavorites() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String? favoritesJson = prefs.getString(_favoritesKey);
      if (favoritesJson == null) return [];
      
      final List<dynamic> favoritesList = jsonDecode(favoritesJson);
      return favoritesList.map((json) => SunshineSpot.fromJson(json)).toList();
    } catch (e) {
      return [];
    }
  }

  static Future<void> addToFavorites(SunshineSpot spot) async {
    final favorites = await getFavorites();
    if (!favorites.any((fav) => fav.id == spot.id)) {
      favorites.add(spot.copyWith(isFavorite: true));
      await _saveFavorites(favorites);
      TelemetryService.logFavoriteAction('added', spot.id, spot.name);
    }
  }

  static Future<void> removeFromFavorites(String spotId) async {
    final favorites = await getFavorites();
    final removedSpot = favorites.where((fav) => fav.id == spotId).isNotEmpty 
        ? favorites.firstWhere((fav) => fav.id == spotId).name 
        : 'Unknown Spot';
    favorites.removeWhere((fav) => fav.id == spotId);
    await _saveFavorites(favorites);
    TelemetryService.logFavoriteAction('removed', spotId, removedSpot);
  }

  static Future<void> _saveFavorites(List<SunshineSpot> favorites) async {
    final prefs = await SharedPreferences.getInstance();
    final String favoritesJson = jsonEncode(favorites.map((fav) => fav.toJson()).toList());
    await prefs.setString(_favoritesKey, favoritesJson);
  }
}