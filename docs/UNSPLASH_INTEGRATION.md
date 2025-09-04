# Unsplash API Integration Guide
*Technical implementation for Sun Chaser photo management*

## Overview

This document provides detailed implementation steps for integrating the Unsplash API into Sun Chaser, ensuring compliance with production requirements and proper attribution.

## Phase 1: Development Setup

### 1. Unsplash Developer Account
1. Visit [Unsplash Developers](https://unsplash.com/developers)
2. Create account and register application
3. Get Access Key and Secret Key
4. Note rate limits: 50 requests/hour for development

### 2. Flutter Dependencies
Add to `Frontend/pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
  url_launcher: ^6.2.1
  cached_network_image: ^3.3.0
```

### 3. Environment Configuration
Create `Frontend/lib/config/unsplash_config.dart`:
```dart
class UnsplashConfig {
  static const String accessKey = String.fromEnvironment('UNSPLASH_ACCESS_KEY');
  static const String baseUrl = 'https://api.unsplash.com';
  static const int resultsPerPage = 10;
  static const String orientation = 'landscape';
}
```

## Phase 2: Core Implementation

### 1. Data Models
Create `Frontend/lib/models/unsplash_photo.dart`:
```dart
class UnsplashPhoto {
  final String id;
  final String description;
  final String altDescription;
  final UnsplashUrls urls;
  final UnsplashUser user;
  final UnsplashLinks links;
  
  UnsplashPhoto({
    required this.id,
    required this.description,
    required this.altDescription,
    required this.urls,
    required this.user,
    required this.links,
  });
  
  factory UnsplashPhoto.fromJson(Map<String, dynamic> json) {
    return UnsplashPhoto(
      id: json['id'],
      description: json['description'] ?? '',
      altDescription: json['alt_description'] ?? '',
      urls: UnsplashUrls.fromJson(json['urls']),
      user: UnsplashUser.fromJson(json['user']),
      links: UnsplashLinks.fromJson(json['links']),
    );
  }
}

class UnsplashUrls {
  final String raw;
  final String full;
  final String regular;
  final String small;
  final String thumb;
  
  UnsplashUrls({
    required this.raw,
    required this.full,
    required this.regular,
    required this.small,
    required this.thumb,
  });
  
  factory UnsplashUrls.fromJson(Map<String, dynamic> json) {
    return UnsplashUrls(
      raw: json['raw'],
      full: json['full'],
      regular: json['regular'],
      small: json['small'],
      thumb: json['thumb'],
    );
  }
}

class UnsplashUser {
  final String id;
  final String name;
  final String username;
  final UnsplashUserLinks links;
  
  UnsplashUser({
    required this.id,
    required this.name,
    required this.username,
    required this.links,
  });
  
  factory UnsplashUser.fromJson(Map<String, dynamic> json) {
    return UnsplashUser(
      id: json['id'],
      name: json['name'],
      username: json['username'],
      links: UnsplashUserLinks.fromJson(json['links']),
    );
  }
}

class UnsplashUserLinks {
  final String html;
  
  UnsplashUserLinks({required this.html});
  
  factory UnsplashUserLinks.fromJson(Map<String, dynamic> json) {
    return UnsplashUserLinks(html: json['html']);
  }
}

class UnsplashLinks {
  final String html;
  final String download;
  final String downloadLocation;
  
  UnsplashLinks({
    required this.html,
    required this.download,
    required this.downloadLocation,
  });
  
  factory UnsplashLinks.fromJson(Map<String, dynamic> json) {
    return UnsplashLinks(
      html: json['html'],
      download: json['download'],
      downloadLocation: json['download_location'],
    );
  }
}
```

### 2. Unsplash Service
Create `Frontend/lib/services/unsplash_service.dart`:
```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/unsplash_photo.dart';
import '../config/unsplash_config.dart';

class UnsplashService {
  static const String _userAgent = 'SunChaser/1.0';
  
  /// Search for photos by location and category
  Future<List<UnsplashPhoto>> searchPhotos({
    required String query,
    String? category,
    int page = 1,
  }) async {
    try {
      final searchQuery = _buildSearchQuery(query, category);
      final uri = Uri.parse(
        '${UnsplashConfig.baseUrl}/search/photos'
      ).replace(queryParameters: {
        'client_id': UnsplashConfig.accessKey,
        'query': searchQuery,
        'page': page.toString(),
        'per_page': UnsplashConfig.resultsPerPage.toString(),
        'orientation': UnsplashConfig.orientation,
        'order_by': 'relevant',
      });
      
      final response = await http.get(
        uri,
        headers: {'User-Agent': _userAgent},
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> results = data['results'];
        
        return results
            .map((photo) => UnsplashPhoto.fromJson(photo))
            .where((photo) => _isRelevantPhoto(photo, category))
            .toList();
      } else {
        throw Exception('Failed to search photos: ${response.statusCode}');
      }
    } catch (e) {
      print('Error searching Unsplash photos: $e');
      return [];
    }
  }
  
  /// Trigger download tracking (REQUIRED for production)
  Future<void> triggerDownload(String photoId, String downloadLocation) async {
    try {
      final uri = Uri.parse(downloadLocation).replace(queryParameters: {
        'client_id': UnsplashConfig.accessKey,
      });
      
      await http.get(
        uri,
        headers: {'User-Agent': _userAgent},
      );
    } catch (e) {
      print('Error triggering download: $e');
    }
  }
  
  String _buildSearchQuery(String query, String? category) {
    final keywords = [query];
    
    // Add category-specific keywords
    if (category != null) {
      switch (category.toLowerCase()) {
        case 'mountain':
          keywords.addAll(['mountain', 'peak', 'summit', 'alpine']);
          break;
        case 'lake':
          keywords.addAll(['lake', 'water', 'reflection']);
          break;
        case 'forest':
          keywords.addAll(['forest', 'trees', 'woodland', 'nature']);
          break;
        case 'beach':
          keywords.addAll(['beach', 'ocean', 'coast', 'shore']);
          break;
        case 'trail':
          keywords.addAll(['trail', 'hiking', 'path', 'outdoor']);
          break;
        // Add more categories...
      }
    }
    
    // Add general outdoor keywords
    keywords.addAll(['outdoor', 'nature', 'landscape', 'pacific northwest']);
    
    return keywords.join(' ');
  }
  
  bool _isRelevantPhoto(UnsplashPhoto photo, String? category) {
    // Add relevance scoring logic
    final description = (photo.description + ' ' + photo.altDescription).toLowerCase();
    
    if (category != null) {
      final categoryKeywords = _getCategoryKeywords(category);
      return categoryKeywords.any((keyword) => description.contains(keyword));
    }
    
    return true;
  }
  
  List<String> _getCategoryKeywords(String category) {
    switch (category.toLowerCase()) {
      case 'mountain':
        return ['mountain', 'peak', 'summit', 'alpine', 'rock', 'cliff'];
      case 'lake':
        return ['lake', 'water', 'pond', 'reflection', 'calm'];
      case 'forest':
        return ['forest', 'tree', 'wood', 'pine', 'cedar', 'fir'];
      case 'beach':
        return ['beach', 'ocean', 'sea', 'coast', 'shore', 'sand'];
      case 'trail':
        return ['trail', 'path', 'hiking', 'walk', 'trek'];
      default:
        return ['outdoor', 'nature', 'landscape'];
    }
  }
}
```

### 3. Enhanced Location Image Service
Update `Frontend/lib/services/location_image_service.dart`:
```dart
import 'unsplash_service.dart';
import '../models/unsplash_photo.dart';

class LocationImageService {
  static final UnsplashService _unsplashService = UnsplashService();
  static final Map<String, UnsplashPhoto> _photoCache = {};
  
  /// Get photo for a specific location
  Future<LocationImage> getLocationImage(String locationName, String category) async {
    final cacheKey = '${locationName}_$category';
    
    // Check cache first
    if (_photoCache.containsKey(cacheKey)) {
      final photo = _photoCache[cacheKey]!;
      return LocationImage(
        url: photo.urls.regular,
        attribution: _buildAttribution(photo),
        photoId: photo.id,
        downloadLocation: photo.links.downloadLocation,
      );
    }
    
    // Search Unsplash
    try {
      final photos = await _unsplashService.searchPhotos(
        query: locationName,
        category: category,
      );
      
      if (photos.isNotEmpty) {
        final selectedPhoto = photos.first;
        _photoCache[cacheKey] = selectedPhoto;
        
        return LocationImage(
          url: selectedPhoto.urls.regular,
          attribution: _buildAttribution(selectedPhoto),
          photoId: selectedPhoto.id,
          downloadLocation: selectedPhoto.links.downloadLocation,
        );
      }
    } catch (e) {
      print('Failed to get Unsplash photo: $e');
    }
    
    // Fallback to category image
    return _getCategoryFallback(category);
  }
  
  /// Track photo usage (REQUIRED for production)
  Future<void> trackPhotoUsage(String photoId, String downloadLocation) async {
    await _unsplashService.triggerDownload(photoId, downloadLocation);
  }
  
  PhotoAttribution _buildAttribution(UnsplashPhoto photo) {
    return PhotoAttribution(
      photographerName: photo.user.name,
      photographerUrl: photo.user.links.html,
      unsplashUrl: photo.links.html,
    );
  }
  
  // ... existing fallback methods
}

class LocationImage {
  final String url;
  final PhotoAttribution attribution;
  final String? photoId;
  final String? downloadLocation;
  
  LocationImage({
    required this.url,
    required this.attribution,
    this.photoId,
    this.downloadLocation,
  });
}

class PhotoAttribution {
  final String photographerName;
  final String photographerUrl;
  final String unsplashUrl;
  
  PhotoAttribution({
    required this.photographerName,
    required this.photographerUrl,
    required this.unsplashUrl,
  });
}
```

## Phase 3: UI Components

### 1. Photo Attribution Widget
Create `Frontend/lib/widgets/photo_attribution.dart`:
```dart
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/location_image_service.dart';

class PhotoAttributionWidget extends StatelessWidget {
  final PhotoAttribution attribution;
  
  const PhotoAttributionWidget({
    Key? key,
    required this.attribution,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(8.0),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.7),
        borderRadius: BorderRadius.circular(4.0),
      ),
      child: Text.rich(
        TextSpan(
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
          ),
          children: [
            const TextSpan(text: 'Photo by '),
            TextSpan(
              text: attribution.photographerName,
              style: const TextStyle(
                decoration: TextDecoration.underline,
                color: Colors.white,
              ),
              recognizer: TapGestureRecognizer()
                ..onTap = () => _launchUrl(attribution.photographerUrl),
            ),
            const TextSpan(text: ' on '),
            TextSpan(
              text: 'Unsplash',
              style: const TextStyle(
                decoration: TextDecoration.underline,
                color: Colors.white,
              ),
              recognizer: TapGestureRecognizer()
                ..onTap = () => _launchUrl(attribution.unsplashUrl),
            ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
```

### 2. Enhanced Sunshine Spot Card
Update `Frontend/lib/widgets/sunshine_spot_card.dart`:
```dart
// Add photo usage tracking
class _SunshineSpotCardState extends State<SunshineSpotCard> {
  LocationImage? _locationImage;
  bool _imageTracked = false;
  
  @override
  void initState() {
    super.initState();
    _loadLocationImage();
  }
  
  Future<void> _loadLocationImage() async {
    try {
      final image = await LocationImageService().getLocationImage(
        widget.spot.name,
        widget.spot.category,
      );
      
      if (mounted) {
        setState(() {
          _locationImage = image;
        });
        
        // Track usage when image is displayed
        _trackPhotoUsage();
      }
    } catch (e) {
      print('Error loading location image: $e');
    }
  }
  
  Future<void> _trackPhotoUsage() async {
    if (_locationImage?.photoId != null && 
        _locationImage?.downloadLocation != null && 
        !_imageTracked) {
      
      await LocationImageService().trackPhotoUsage(
        _locationImage!.photoId!,
        _locationImage!.downloadLocation!,
      );
      
      _imageTracked = true;
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          // Image with attribution
          Stack(
            children: [
              // Main image
              CachedNetworkImage(
                imageUrl: _locationImage?.url ?? _getCategoryFallbackUrl(),
                height: 200,
                width: double.infinity,
                fit: BoxFit.cover,
                placeholder: (context, url) => _buildImagePlaceholder(),
                errorWidget: (context, url, error) => _buildErrorWidget(),
              ),
              
              // Attribution overlay
              if (_locationImage?.attribution != null)
                Positioned(
                  bottom: 4,
                  right: 4,
                  child: PhotoAttributionWidget(
                    attribution: _locationImage!.attribution,
                  ),
                ),
            ],
          ),
          
          // ... rest of card content
        ],
      ),
    );
  }
}
```

## Phase 4: Production Requirements

### 1. Production Application Checklist

**Before applying for production access:**
- [ ] Implement photo hotlinking (using Unsplash URLs directly)
- [ ] Add download tracking for all viewed photos
- [ ] Ensure app design is visually distinct from Unsplash
- [ ] Remove any "Unsplash" branding from app name/UI
- [ ] Implement proper attribution on all photos
- [ ] Prepare screenshots showing attribution
- [ ] Write accurate app description

### 2. Application Materials

**App Description Template:**
```
Sun Chaser - Outdoor Recreation Finder

Sun Chaser is a mobile application that helps outdoor enthusiasts discover hiking trails, 
parks, lakes, and other recreational locations in the Pacific Northwest. The app provides 
weather-aware recommendations for outdoor activities based on user location and preferences.

We use Unsplash's API to display high-quality landscape photography that represents the 
natural beauty of recommended locations. All photos are properly attributed to their 
photographers and link back to Unsplash as required.

Key Features:
- Location-based outdoor recreation recommendations
- Weather integration for activity planning
- High-quality location photography via Unsplash API
- Proper photographer attribution and Unsplash crediting

Usage: We expect approximately 1,000-2,000 photo requests per day as users browse 
location recommendations. Photos are cached on device to minimize repeated requests.
```

### 3. Rate Limit Management
```dart
class UnsplashRateLimitManager {
  static int _requestCount = 0;
  static DateTime _lastReset = DateTime.now();
  static const int _hourlyLimit = 5000; // Production limit
  
  static bool canMakeRequest() {
    _resetCounterIfNeeded();
    return _requestCount < _hourlyLimit;
  }
  
  static void recordRequest() {
    _requestCount++;
  }
  
  static void _resetCounterIfNeeded() {
    final now = DateTime.now();
    if (now.difference(_lastReset).inHours >= 1) {
      _requestCount = 0;
      _lastReset = now;
    }
  }
}
```

## Next Steps

1. **Register Unsplash Developer Account**
2. **Implement Phase 1: Basic API Integration**
3. **Test with development rate limits**
4. **Implement Phase 2: Production Requirements**
5. **Submit production application**
6. **Deploy with production API keys**

---

**Status**: Ready for development
**Estimated Timeline**: 2-3 weeks for full implementation
**Dependencies**: Unsplash Developer Account registration
