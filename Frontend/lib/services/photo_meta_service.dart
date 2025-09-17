import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:sunshine_spotter/config.dart';

/// Small interface to fetch photo metadata (attribution, urls, etc).
/// Implementations may call the backend or return canned responses in tests.
abstract class PhotoMetaService {
  /// Fetch metadata for [photoId] in [category]. Returns decoded JSON map
  /// on success, or null on non-200 / error.
  Future<Map<String, dynamic>?> fetchMeta(String photoId, String category);
}

class HttpPhotoMetaService implements PhotoMetaService {
  final Duration timeout;

  HttpPhotoMetaService({this.timeout = const Duration(seconds: 3)});

  @override
  Future<Map<String, dynamic>?> fetchMeta(String photoId, String category) async {
    try {
      final base = apiBaseUrl();
      final uri = Uri.parse(base).replace(path: '/internal/photos/meta', queryParameters: {
        'photo_id': photoId,
        'category': category,
      });
      final resp = await http.get(uri).timeout(timeout);
      if (resp.statusCode == 200) {
        return jsonDecode(resp.body) as Map<String, dynamic>;
      }
      return null;
    } catch (_) {
      return null;
    }
  }
}
