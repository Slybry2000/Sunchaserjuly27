import 'dart:developer' as developer;
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Optional backend telemetry ingestion base URL. If null, events are only
/// written to developer.log. Set this from app configuration at startup.
String? telemetryBaseUrl;

class TelemetryService {
  TelemetryService._();

  /// Generic event logger. Accepts an optional named `properties` map to match
  /// call sites in the codebase.
  static void logEvent(String name, {Map<String, dynamic>? properties}) {
    final payload = {
      'event': name,
      'properties': properties ?? {},
      'timestamp': DateTime.now().toIso8601String(),
      'source': 'flutter_client'
    };
    developer.log('Telemetry event: $name ${properties ?? {}}', name: 'TelemetryService');
    _maybePost(payload);
  }

  /// Cache-related telemetry used by the API client.
  static void logCacheEvent(String action, String key, {bool hit = false}) {
  final payload = {'event': 'cache_event', 'properties': {'action': action, 'key': key, 'hit': hit}};
  developer.log('CacheEvent action=$action key=$key hit=$hit', name: 'TelemetryService');
  _maybePost(payload);
  }

  /// API call timing and result telemetry.
  static void logApiCall(String endpoint, Duration elapsed, {bool success = true, String? error}) {
    final payload = {
      'event': 'api_call',
      'properties': {'endpoint': endpoint, 'elapsed_ms': elapsed.inMilliseconds, 'success': success, 'error': error}
    };
    developer.log('ApiCall endpoint=$endpoint elapsed=${elapsed.inMilliseconds}ms success=$success error=$error', name: 'TelemetryService');
    _maybePost(payload);
  }

  /// Record an error. Keep it lightweight for CI/local runs.
  static void logError(String message, {String? context, Object? exception, StackTrace? stack}) {
    final payload = {
      'event': 'error',
      'properties': {'message': message, 'context': context, 'exception': exception?.toString()}
    };
    developer.log('Error: $message context=$context exception=$exception', name: 'TelemetryService', error: exception, stackTrace: stack);
    _maybePost(payload);
  }

  /// Specialized search telemetry used by the UI.
  static void logSearch({
    required double latitude,
    required double longitude,
    required double radius,
    required int resultsCount,
    required Duration searchDuration,
  }) {
    final payload = {
      'event': 'search',
      'properties': {
        'latitude': latitude,
        'longitude': longitude,
        'radius': radius,
        'results': resultsCount,
        'duration_ms': searchDuration.inMilliseconds
      }
    };
    developer.log('Search latitude=$latitude longitude=$longitude radius=$radius results=$resultsCount duration_ms=${searchDuration.inMilliseconds}', name: 'TelemetryService');
    _maybePost(payload);
  }

  /// Favorite add/remove telemetry.
  static void logFavoriteAction(String action, String id, String? title) {
    final payload = {'event': 'favorite', 'properties': {'action': action, 'id': id, 'title': title}};
    developer.log('FavoriteAction action=$action id=$id title=$title', name: 'TelemetryService');
    _maybePost(payload);
  }

  static Future<void> _maybePost(Map<String, dynamic> payload) async {
    if (telemetryBaseUrl == null) return;
    // Do not await to avoid blocking UI; fire-and-forget with minimal error handling
    unawaited(_post(telemetryBaseUrl!, payload));
  }

  static Future<void> _post(String baseUrl, Map<String, dynamic> payload) async {
    try {
      final uri = Uri.parse(baseUrl).replace(path: '/telemetry');
      await http.post(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode(payload)).timeout(Duration(seconds: 3));
    } catch (e) {
      developer.log('Telemetry post failed: $e', name: 'TelemetryService');
    }
  }
}
