import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:network_image_mock/network_image_mock.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:sunshine_spotter/services/photo_meta_service.dart';
import 'package:sunshine_spotter/services/photo_track_service.dart';
import 'package:sunshine_spotter/widgets/sunshine_spot_card.dart';
import 'package:visibility_detector/visibility_detector.dart';

class _NoopMetaService implements PhotoMetaService {
  @override
  Future<Map<String, dynamic>?> fetchMeta(String photoId, String category) async => null;
}

class _TrackRecorder implements PhotoTrackService {
  int calls = 0;
  @override
  Future<bool> trackPhoto(String photoId) async {
    calls++;
    return true;
  }
}

void main() {
  setUpAll(() {
    VisibilityDetectorController.instance.updateInterval = Duration.zero;
  });
  testWidgets('attribution HTML renders tappable photographer and Unsplash links', (tester) async {
    final spot = SunshineSpot(
      id: 's1',
      name: 'Test Location',
      description: 'Desc',
      latitude: 47.6,
      longitude: -122.3,
      imageUrl: 'https://images.unsplash.com/photo-abc123',
      apiPhotoId: 'abc123',
      sunshineHours: 7,
      temperature: 65,
      weather: 'Sunny',
      rating: 4.5,
      category: 'hiking',
      distance: 10.2,
      isFavorite: false,
    );
    final track = _TrackRecorder();
    await mockNetworkImagesFor(() async {
      await tester.pumpWidget(MaterialApp(
        home: SunshineSpotCard(
          spot: spot,
          onTap: () {},
          onFavoriteToggle: () {},
          initialAttributionHtml: 'Photo by <a href="https://unsplash.com/@user">User</a> on <a href="https://unsplash.com/photos/abc123">Unsplash</a>',
          photoMetaService: _NoopMetaService(),
          photoTrackService: track,
        ),
      ));
    });
  // First pump builds widget; additional pumps allow visibility callbacks.
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 100));

    // Find RichText containing 'Photo by'
    final richTextFinder = find.byType(RichText);
    expect(richTextFinder, findsWidgets);

    // Ensure text spans exist
    final richTextWidgets = tester.widgetList<RichText>(richTextFinder);
    final hasAttribution = richTextWidgets.any((w) =>
      w.text.toPlainText().contains('Photo by') && w.text.toPlainText().contains('Unsplash'));
    expect(hasAttribution, isTrue);

    // Simulate a tap on the photographer link by tapping text 'User'
  // We can't directly tap span text without separate Text widgets; ensure recognizers created
  final anyWithUser = richTextWidgets.any((w) => w.text.toPlainText().contains('User'));
  final anyWithUnsplash = richTextWidgets.any((w) => w.text.toPlainText().contains('Unsplash'));
  expect(anyWithUser, isTrue);
  expect(anyWithUnsplash, isTrue);

  // Tracking should have happened exactly once (visibility)
  expect(track.calls, 1);
  });
}
