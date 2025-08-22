import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/recommend_response.dart';

class ApiClient {
  final String baseUrl;
  final http.Client _httpClient;

  ApiClient({required this.baseUrl, http.Client? httpClient}) : _httpClient = httpClient ?? http.Client();

  String _canonicalKey(double lat, double lon, int radius) => 'recommend:${lat.toStringAsFixed(4)}:${lon.toStringAsFixed(4)}:$radius';

  Future<RecommendResponse?> recommend(double lat, double lon, {int radius = 100}) async {
    final prefs = await SharedPreferences.getInstance();
    final key = _canonicalKey(lat, lon, radius);
    final storedEtag = prefs.getString('$key:etag');
    final storedBody = prefs.getString('$key:body');

    final uri = Uri.parse('$baseUrl/recommend?lat=$lat&lon=$lon&radius=$radius');
    final headers = <String, String>{'Accept': 'application/json'};
    if (storedEtag != null) headers['If-None-Match'] = storedEtag;

    final resp = await _httpClient.get(uri, headers: headers);

    if (resp.statusCode == 200) {
      final etag = resp.headers['etag'];
      final body = resp.body;
      if (etag != null) {
        await prefs.setString('$key:etag', etag);
        await prefs.setString('$key:body', body);
      }
      final json = jsonDecode(body) as Map<String, dynamic>;
      return RecommendResponse.fromJson(json);
    } else if (resp.statusCode == 304) {
      if (storedBody != null) {
        final json = jsonDecode(storedBody) as Map<String, dynamic>;
        return RecommendResponse.fromJson(json);
      }
      return null;
    } else {
      // Handle errors as needed
      return null;
    }
  }
}
// ci-touch 2025-08-22T00:01:34.5150224-07:00
