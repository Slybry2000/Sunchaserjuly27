import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/recommend_response.dart';
import 'telemetry_service.dart';

class ApiClient {
  final String baseUrl;
  final http.Client _httpClient;

  ApiClient({required this.baseUrl, http.Client? httpClient}) : _httpClient = httpClient ?? http.Client();

  static const String _ver = 'v2';
  // New (versioned) cache key format
  String _canonicalKey(double lat, double lon, int radius) => 'recommend:${_ver}:${lat.toStringAsFixed(4)}:${lon.toStringAsFixed(4)}:$radius';
  String _canonicalKeyForQuery(String q, int radius) => 'recommend:${_ver}:q:${q.trim().toLowerCase()}:$radius';
  // Legacy (unversioned) key format still used by older tests / installations
  String _legacyKey(double lat, double lon, int radius) => 'recommend:${lat.toStringAsFixed(4)}:${lon.toStringAsFixed(4)}:$radius';
  String _legacyKeyForQuery(String q, int radius) => 'recommend:q:${q.trim().toLowerCase()}:$radius';

  Future<RecommendResponse?> recommend(double lat, double lon, {int radius = 100, String? q}) async {
    final stopwatch = Stopwatch()..start();
    final endpoint = '/recommend';
    
    try {
      final prefs = await SharedPreferences.getInstance();
      final String key;
      Uri uri;
      if (q != null && q.trim().isNotEmpty) {
        key = _canonicalKeyForQuery(q, radius);
        final qp = {'q': q.trim(), 'radius': radius.toString()};
        uri = Uri.parse(baseUrl).replace(path: '/recommend', queryParameters: qp);
      } else {
        key = _canonicalKey(lat, lon, radius);
        uri = Uri.parse(baseUrl).replace(path: '/recommend', queryParameters: {
          'lat': lat.toString(),
          'lon': lon.toString(),
          'radius': radius.toString(),
        });
      }

      // Attempt primary (versioned) lookup first
      String? storedEtag = prefs.getString('$key:etag');
      String? storedBody = prefs.getString('$key:body');

      // Back-compat: if not found, fall back to legacy key naming so existing
      // tests (which pre-populate legacy keys) still work while we migrate.
      if (storedEtag == null || storedBody == null) {
        final legacyKey = (q != null && q.trim().isNotEmpty)
            ? _legacyKeyForQuery(q, radius)
            : _legacyKey(lat, lon, radius);
        storedEtag ??= prefs.getString('$legacyKey:etag');
        storedBody ??= prefs.getString('$legacyKey:body');
      }
      final headers = <String, String>{'Accept': 'application/json'};
      if (storedEtag != null) {
        headers['If-None-Match'] = storedEtag;
        TelemetryService.logCacheEvent('check', key);
      }

  final resp = await _httpClient.get(uri, headers: headers);
      stopwatch.stop();

      if (resp.statusCode == 200) {
        final etag = resp.headers['etag'];
        final body = resp.body;
        if (etag != null) {
          // Store under both new and legacy keys for transition period.
          await prefs.setString('$key:etag', etag);
          await prefs.setString('$key:body', body);
          final legacyKey = (q != null && q.trim().isNotEmpty)
              ? _legacyKeyForQuery(q, radius)
              : _legacyKey(lat, lon, radius);
            await prefs.setString('$legacyKey:etag', etag);
            await prefs.setString('$legacyKey:body', body);
          TelemetryService.logCacheEvent('store', key);
        }
        final json = jsonDecode(body) as Map<String, dynamic>;
        final response = RecommendResponse.fromJson(json);
        
        TelemetryService.logApiCall(endpoint, stopwatch.elapsed, success: true);
        return response;
      } else if (resp.statusCode == 304) {
        TelemetryService.logCacheEvent('hit', key, hit: true);
        if (storedBody != null) {
          final json = jsonDecode(storedBody) as Map<String, dynamic>;
          final response = RecommendResponse.fromJson(json);
          
          TelemetryService.logApiCall(endpoint, stopwatch.elapsed, success: true);
          return response;
        }
        TelemetryService.logApiCall(endpoint, stopwatch.elapsed, success: false, error: '304 with no cached body');
        return null;
      } else {
        TelemetryService.logApiCall(endpoint, stopwatch.elapsed, success: false, error: 'HTTP ${resp.statusCode}');
        return null;
      }
    } catch (e) {
      stopwatch.stop();
      TelemetryService.logError('API call failed', context: endpoint, exception: e);
      TelemetryService.logApiCall(endpoint, stopwatch.elapsed, success: false, error: e.toString());
      return null;
    }
  }
}
// ci-touch 2025-08-22T00:01:34.5150224-07:00
