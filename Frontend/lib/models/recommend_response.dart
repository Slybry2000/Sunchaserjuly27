class RecommendationResult {
  final String id;
  final String name;
  final double lat;
  final double lon;
  final double elevation;
  final String category;
  final String state;
  final String timezone;
  final double distanceMi;
  final String? sunStartIso;
  final int durationHours;
  final double score;
  final String? photoId;

  RecommendationResult({
    required this.id,
    required this.name,
    required this.lat,
    required this.lon,
    required this.elevation,
    required this.category,
    required this.state,
    required this.timezone,
    required this.distanceMi,
    required this.sunStartIso,
    required this.durationHours,
  required this.score,
  this.photoId,
  });

  factory RecommendationResult.fromJson(Map<String, dynamic> json) => RecommendationResult(
        id: json['id'] as String,
        name: json['name'] as String,
  // TODO-6: Review numeric casts for null-safety and parse errors (see docs/INLINE_TODO_ISSUES.md)
  lat: (json['lat'] as num).toDouble(),
  lon: (json['lon'] as num).toDouble(),
  elevation: (json['elevation'] as num).toDouble(),
        category: json['category'] as String,
        state: json['state'] as String,
        timezone: json['timezone'] as String,
        distanceMi: (json['distance_mi'] as num).toDouble(),
        sunStartIso: json['sun_start_iso'] as String?,
        durationHours: (json['duration_hours'] as num).toInt(),
        score: (json['score'] as num).toDouble(),
        photoId: json['photo_id'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'lat': lat,
        'lon': lon,
        'elevation': elevation,
        'category': category,
        'state': state,
        'timezone': timezone,
        'distance_mi': distanceMi,
        'sun_start_iso': sunStartIso,
        'duration_hours': durationHours,
        'score': score,
  'photo_id': photoId,
      };
}

class RecommendResponse {
  final Map<String, dynamic> query;
  final List<RecommendationResult> results;
  final String generatedAt;
  final String version;

  RecommendResponse({
    required this.query,
    required this.results,
    required this.generatedAt,
    required this.version,
  });

  factory RecommendResponse.fromJson(Map<String, dynamic> json) => RecommendResponse(
        query: Map<String, dynamic>.from(json['query'] as Map),
        results: (json['results'] as List)
            .map((e) => RecommendationResult.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
        generatedAt: json['generated_at'] as String,
        version: json['version'] as String,
      );

  Map<String, dynamic> toJson() => {
        'query': query,
        'results': results.map((r) => r.toJson()).toList(),
        'generated_at': generatedAt,
        'version': version,
      };
}
