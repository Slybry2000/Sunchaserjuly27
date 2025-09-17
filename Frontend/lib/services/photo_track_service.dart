import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:sunshine_spotter/config.dart';

abstract class PhotoTrackService {
  /// Send a tracking event for [photoId]. Return true on success.
  Future<bool> trackPhoto(String photoId);
}

class HttpPhotoTrackService implements PhotoTrackService {
  final Duration timeout;

  HttpPhotoTrackService({this.timeout = const Duration(seconds: 2)});

  @override
  Future<bool> trackPhoto(String photoId) async {
    try {
      final base = apiBaseUrl();
      final uri = Uri.parse(base).replace(path: '/internal/photos/track');
      final body = jsonEncode({'photo_id': photoId});
      final resp = await http.post(uri, headers: {'Content-Type': 'application/json'}, body: body).timeout(timeout);
      return resp.statusCode >= 200 && resp.statusCode < 300;
    } catch (_) {
      return false;
    }
  }
}
