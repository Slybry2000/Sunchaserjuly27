import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'package:sunshine_spotter/services/api_client.dart';
import 'dart:typed_data';
// ...existing imports...

class _FakeClient implements http.Client {
  final http.Response responseToReturn;
  _FakeClient(this.responseToReturn);

  @override
  Future<http.Response> get(Uri url, {Map<String, String>? headers}) async {
    return responseToReturn;
  }

  @override
  Future<String> read(Uri url, {Map<String, String>? headers}) {
    return Future.value(responseToReturn.body);
  }

  @override
  Future<Uint8List> readBytes(Uri url, {Map<String, String>? headers}) {
    return Future.value(Uint8List.fromList(responseToReturn.bodyBytes));
  }

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    // Convert the preconfigured response into a StreamedResponse
    final stream = Stream.fromIterable([responseToReturn.bodyBytes]);
    return http.StreamedResponse(stream, responseToReturn.statusCode, headers: responseToReturn.headers);
  }

  // The rest are not used in these tests
  @override
  void close() {}

  @override
  Future<http.Response> head(Uri url, {Map<String, String>? headers}) {
    throw UnimplementedError();
  }

  @override
  Future<http.Response> post(Uri url,
      {Map<String, String>? headers, Object? body, Encoding? encoding}) {
    throw UnimplementedError();
  }

  @override
  Future<http.Response> put(Uri url,
      {Map<String, String>? headers, Object? body, Encoding? encoding}) {
    throw UnimplementedError();
  }

  @override
  Future<http.Response> patch(Uri url,
      {Map<String, String>? headers, Object? body, Encoding? encoding}) {
    throw UnimplementedError();
  }

  @override
  Future<http.Response> delete(Uri url,
      {Map<String, String>? headers, Object? body, Encoding? encoding}) {
    throw UnimplementedError();
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('ApiClient ETag behavior', () {
    setUp(() async {
      SharedPreferences.setMockInitialValues({});
    });

    test('stores etag and body on 200 response', () async {
      final fixture = {
        'query': {'lat': 1.0, 'lon': 2.0, 'radius': 100},
        'results': [
          {
            'id': 'T1',
            'name': 'Test Spot',
            'lat': 1.1,
            'lon': 2.1,
            'elevation': 1200.0,
            'category': 'Forest',
            'state': 'WA',
            'timezone': 'America/Los_Angeles',
            'distance_mi': 5.0,
            'sun_start_iso': null,
            'duration_hours': 3,
            'score': 10.5
          }
        ],
        'generated_at': '2025-08-21T12:00:00Z',
        'version': 'v1'
      };

      final resp = http.Response(jsonEncode(fixture), 200, headers: {'etag': '"abc123"'});
      final client = ApiClient(baseUrl: 'http://localhost:8000', httpClient: _FakeClient(resp));

      final result = await client.recommend(1.0, 2.0, radius: 100);
      expect(result, isNotNull);
      expect(result!.results.length, 1);

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('recommend:1.0000:2.0000:100:etag'), '"abc123"');
      expect(prefs.getString('recommend:1.0000:2.0000:100:body'), isNotNull);
    });

    test('returns cached body on 304', () async {
      final fixture = {
        'query': {'lat': 1.0, 'lon': 2.0, 'radius': 100},
        'results': [
          {
            'id': 'T2',
            'name': 'Cached Spot',
            'lat': 1.2,
            'lon': 2.2,
            'elevation': 800.0,
            'category': 'Beach',
            'state': 'OR',
            'timezone': 'America/Los_Angeles',
            'distance_mi': 6.0,
            'sun_start_iso': null,
            'duration_hours': 2,
            'score': 8.0
          }
        ],
        'generated_at': '2025-08-21T12:00:00Z',
        'version': 'v1'
      };

      final keyBase = 'recommend:1.0000:2.0000:100';
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('$keyBase:etag', '"cached"');
      await prefs.setString('$keyBase:body', jsonEncode(fixture));

      final resp = http.Response('', 304);
      final client = ApiClient(baseUrl: 'http://localhost:8000', httpClient: _FakeClient(resp));

      final result = await client.recommend(1.0, 2.0, radius: 100);
      expect(result, isNotNull);
      expect(result!.results.first.id, 'T2');
    });
  });
}
