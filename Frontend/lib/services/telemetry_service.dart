class TelemetryService {
  TelemetryService._();

  static void logCacheEvent(String event, String key, {bool hit = false}) {
    // No-op in CI; implement real telemetry in frontend integration.
    // print('[telemetry] cache=$event key=$key hit=$hit');
  }

  static void logApiCall(String endpoint, Duration elapsed, {bool success = true, String? error}) {
    // No-op or simple logging during development
    // print('[telemetry] api=$endpoint elapsed=${elapsed.inMilliseconds}ms success=$success error=$error');
  }

  static void logError(String message, {String? context, Object? exception}) {
    // No-op
    // print('[telemetry] error=$message context=$context exception=$exception');
  }
}
import 'dart:developer' as developer;

/// Simple telemetry service for client-side logging and basic analytics
class TelemetryService {
  static const String _tag = 'SunshineSpotter';

  /// Log a user action or event
  static void logEvent(String event, {Map<String, dynamic>? properties}) {
    final logMessage = _buildLogMessage(event, properties);
    developer.log(logMessage, name: _tag);
  }

  /// Log an error with context
  static void logError(String error, {String? context, dynamic exception, StackTrace? stackTrace}) {
    final logMessage = _buildErrorMessage(error, context, exception, stackTrace);
    developer.log(logMessage, name: _tag, level: 1000); // ERROR level
  }

  /// Log API call performance
  static void logApiCall(String endpoint, Duration duration, {bool success = true, String? error}) {
    final properties = {
      'endpoint': endpoint,
      'duration_ms': duration.inMilliseconds,
      'success': success,
      if (error != null) 'error': error,
    };
    
    logEvent('api_call', properties: properties);
  }

  /// Log user navigation
  static void logNavigation(String from, String to) {
    logEvent('navigation', properties: {
      'from': from,
      'to': to,
    });
  }

  /// Log search activity
  static void logSearch({
    required double latitude,
    required double longitude,
    required double radius,
    required int resultsCount,
    required Duration searchDuration,
  }) {
    logEvent('search', properties: {
      'latitude': latitude.toStringAsFixed(4),
      'longitude': longitude.toStringAsFixed(4),
      'radius_miles': radius,
      'results_count': resultsCount,
      'search_duration_ms': searchDuration.inMilliseconds,
    });
  }

  /// Log favorite interactions
  static void logFavoriteAction(String action, String spotId, String spotName) {
    logEvent('favorite_$action', properties: {
      'spot_id': spotId,
      'spot_name': spotName,
    });
  }

  /// Log cache performance
  static void logCacheEvent(String event, String key, {bool hit = false}) {
    logEvent('cache_$event', properties: {
      'cache_key': key,
      'cache_hit': hit,
    });
  }

  static String _buildLogMessage(String event, Map<String, dynamic>? properties) {
    final timestamp = DateTime.now().toIso8601String();
    final buffer = StringBuffer();
    
    buffer.write('[$timestamp] $event');
    
    if (properties != null && properties.isNotEmpty) {
      buffer.write(' - ');
      final props = properties.entries
          .map((e) => '${e.key}=${e.value}')
          .join(', ');
      buffer.write(props);
    }
    
    return buffer.toString();
  }

  static String _buildErrorMessage(String error, String? context, dynamic exception, StackTrace? stackTrace) {
    final timestamp = DateTime.now().toIso8601String();
    final buffer = StringBuffer();
    
    buffer.write('[$timestamp] ERROR: $error');
    
    if (context != null) {
      buffer.write(' (Context: $context)');
    }
    
    if (exception != null) {
      buffer.write(' - Exception: $exception');
    }
    
    if (stackTrace != null) {
      buffer.write('\nStackTrace: $stackTrace');
    }
    
    return buffer.toString();
  }
}
