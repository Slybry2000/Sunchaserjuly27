import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:sunshine_spotter/services/photo_meta_service.dart';
import 'package:sunshine_spotter/services/photo_track_service.dart';
import 'package:sunshine_spotter/widgets/sunshine_spot_card.dart';

class FakeTrackService implements PhotoTrackService {
  final List<String> called = [];
  @override
  Future<bool> trackPhoto(String photoId) async {
    called.add(photoId);
    return true;
  }
}

class FakeMetaServiceWithUrl implements PhotoMetaService {
  final Map<String, dynamic> response;
  FakeMetaServiceWithUrl(this.response);
  @override
  Future<Map<String, dynamic>?> fetchMeta(String photoId, String category) async {
    return response;
  }
}

SunshineSpot _spotWithApi(String? apiId, String image) => SunshineSpot(
  id: 's1',
  name: 'S',
  description: '',
  latitude: 0,
  longitude: 0,
  imageUrl: image,
  apiPhotoId: apiId,
  sunshineHours: 1,
  temperature: 50,
  weather: 'Clear',
  rating: 4.0,
  category: 'beach',
  distance: 1.0,
);

void main() {
  testWidgets('trackPhoto is called when apiPhotoId present', (tester) async {
    final fakeTrack = FakeTrackService();
  final spot = _spotWithApi('abc', 'https://images.unsplash.com/id-abc');

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SunshineSpotCard(
          spot: spot,
          onTap: () {},
          onFavoriteToggle: () {},
          photoTrackService: fakeTrack,
        ),
      ),
    ));

    // Allow image loading to call _track via loadingBuilder
    await tester.pumpAndSettle();
    // The FakeTrackService should have been called with 'abc'
    expect(fakeTrack.called, contains('abc'));
  });

  testWidgets('when meta returns a different urls.regular the image is updated and track is called twice', (tester) async {
    final fakeTrack = FakeTrackService();
    final meta = {
      'source': 'live',
      'attribution_html': 'Photo by <a href="...">P</a>',
      'urls': {'regular': 'https://images.unsplash.com/updated-id'}
    };
    final fakeMeta = FakeMetaServiceWithUrl(meta);

  final spot = _spotWithApi(null, 'https://images.unsplash.com/id-initial');

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SunshineSpotCard(
          spot: spot,
          onTap: () {},
          onFavoriteToggle: () {},
          photoMetaService: fakeMeta,
          photoTrackService: fakeTrack,
        ),
      ),
    ));

    // Let the meta fetch and potential image update complete
    await tester.pumpAndSettle();

  // The track should have been called first for the initial derived id, and
  // then again for the updated id derived from the meta response.
  expect(fakeTrack.called, equals(['id-initial', 'updated-id']));
  });
}
