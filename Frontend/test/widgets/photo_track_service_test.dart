import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:sunshine_spotter/services/photo_meta_service.dart';
import 'package:sunshine_spotter/services/photo_track_service.dart';
import 'package:sunshine_spotter/widgets/sunshine_spot_card.dart';
import 'package:visibility_detector/visibility_detector.dart';

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
  setUpAll(() {
    VisibilityDetectorController.instance.updateInterval = Duration.zero;
  });
  testWidgets('trackPhoto is called when apiPhotoId present (via visibility)', (tester) async {
    final fakeTrack = FakeTrackService();
    final spot = _spotWithApi('abc', 'https://images.unsplash.com/id-abc');

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ListView(
          children: [SizedBox(height: 400, child: SunshineSpotCard(
            spot: spot,
            onTap: () {},
            onFavoriteToggle: () {},
            photoTrackService: fakeTrack,
          ))],
        ),
      ),
    ));

    // Initial pump builds widgets and visibility detector registers.
  await tester.pump(); // build
  await tester.pump(); // visibility processed immediately
    expect(fakeTrack.called, contains('abc'));
  });

  testWidgets('when meta returns different urls.regular tracking occurs for each visible image', (tester) async {
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

    // First frame -> initial visibility triggers first track.
  await tester.pump(); // build
  await tester.pump(const Duration(milliseconds: 10)); // async meta completes
  await tester.pump(); // updated image visibility
    expect(fakeTrack.called, equals(['id-initial', 'updated-id']));
  });

  testWidgets('visibility only tracks once even after multiple pumps', (tester) async {
    final fakeTrack = FakeTrackService();
    final spot = _spotWithApi('once', 'https://images.unsplash.com/once');

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
  await tester.pump();
  await tester.pump();
  await tester.pump();
    expect(fakeTrack.called.where((e) => e == 'once').length, 1);
  });
}
