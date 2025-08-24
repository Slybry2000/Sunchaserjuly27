import 'dart:developer' as developer;

class TelemetryService {
  TelemetryService._();

  /// Generic event logger. Accepts an optional named `properties` map to match
  /// call sites in the codebase.
  static void logEvent(String name, {Map<String, dynamic>? properties}) {
    developer.log('Telemetry event: $name ${properties ?? {}}', name: 'TelemetryService');
  }

  /// Cache-related telemetry used by the API client.
  static void logCacheEvent(String action, String key, {bool hit = false}) {
    developer.log('CacheEvent action=$action key=$key hit=$hit', name: 'TelemetryService');
  }

  /// API call timing and result telemetry.
  static void logApiCall(String endpoint, Duration elapsed, {bool success = true, String? error}) {
    developer.log('ApiCall endpoint=$endpoint elapsed=${elapsed.inMilliseconds}ms success=$success error=$error', name: 'TelemetryService');
  }

  /// Record an error. Keep it lightweight for CI/local runs.
  static void logError(String message, {String? context, Object? exception, StackTrace? stack}) {
    developer.log('Error: $message context=$context exception=$exception', name: 'TelemetryService', error: exception, stackTrace: stack);
  }

  /// Specialized search telemetry used by the UI.
  static void logSearch({
    required double latitude,
    required double longitude,
    required double radius,
    required int resultsCount,
    required Duration searchDuration,
  }) {
    developer.log('Search latitude=$latitude longitude=$longitude radius=$radius results=$resultsCount duration_ms=${searchDuration.inMilliseconds}', name: 'TelemetryService');
  }

  /// Favorite add/remove telemetry.
  static void logFavoriteAction(String action, String id, String? title) {
    developer.log('FavoriteAction action=$action id=$id title=$title', name: 'TelemetryService');
  }
}
