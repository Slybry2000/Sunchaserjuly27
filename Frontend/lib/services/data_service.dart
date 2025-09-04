import 'dart:convert';
import 'dart:math';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:sunshine_spotter/services/api_client.dart';
import 'package:sunshine_spotter/services/telemetry_service.dart';
import 'package:sunshine_spotter/services/location_image_service.dart';

class DataService {
  static const String _favoritesKey = 'favorites';

  // API base URL can be provided at build/run time via --dart-define=API_BASE_URL
  // Default uses Android emulator host mapping for local dev.
  static final ApiClient _apiClient = ApiClient(
    baseUrl: const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000'),
  );

  static final List<SunshineSpot> _sampleSpots = [
    SunshineSpot(
      id: '1',
      name: 'Sunny Beach Park',
      description: 'Beautiful beachfront park with golden sand and crystal clear waters. Perfect for sunbathing and beach volleyball.',
      latitude: 37.7749,
      longitude: -122.4194,
      imageUrl: 'https://pixabay.com/get/g6743ee2e7625dd0be8d5ee02211e7c0e828923c8cedba49b3b04d833e6b46b84cebba0ac83810df7590f675baa6978d28578dc4f04cf050dc07b2a63836ccd39_1280.jpg',
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
      imageUrl: 'https://pixabay.com/get/gce157442f9d085ed1712dd6bca1b35d1cabbac38cfa254f789f5879fb216a978a34f17807ccdf7183a3cb7cd2555040d07b6f900e580bed49f832db3db218e13_1280.jpg',
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
      imageUrl: 'https://pixabay.com/get/g09f73fa251cb440a0cbae8a5b7d15c97e39c5c9563482bbf33e31b792b3566fefa34714e9d48bdd74507a64b816f76bc229f330a23f8bf4b3176d026f49c05a2_1280.jpg',
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
      imageUrl: 'https://pixabay.com/get/g2a29112cb3c0a000302179b8c458027469ed3949d4a9b73b95b9067741e1dc0b0da556652875679d4ff493fef4f07c3eb203fbd057910bedc434ac74a11093c6_1280.jpg',
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
      imageUrl: 'https://pixabay.com/get/g6743ee2e7625dd0be8d5ee02211e7c0e828923c8cedba49b3b04d833e6b46b84cebba0ac83810df7590f675baa6978d28578dc4f04cf050dc07b2a63836ccd39_1280.jpg',
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
        // Map RecommendResponse -> SunshineSpot
        List<SunshineSpot> spots = resp.results.map((r) {
          final distance = _calculateDistance(latitude, longitude, r.lat, r.lon);
          return SunshineSpot(
            id: r.id,
            name: r.name,
            description: _buildDescription(r),
            latitude: r.lat,
            longitude: r.lon,
            imageUrl: LocationImageService.getLocationImageUrl(r.id, r.category),
            sunshineHours: r.durationHours,
            temperature: 70.0, // Could be enhanced with weather API temperature
            weather: 'Sunny',
            rating: (r.score / 100.0 * 5.0), // Convert 0-100 score to 0-5 rating
            category: r.category, // Use backend category
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
    // TODO: Remove this entire fallback section in next cleanup
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