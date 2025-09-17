import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:sunshine_spotter/services/photo_meta_service.dart';
import 'package:sunshine_spotter/widgets/sunshine_spot_card.dart';

class FakePhotoMetaService implements PhotoMetaService {
  final Map<String, Map<String, dynamic>?> responses;

  FakePhotoMetaService(this.responses);

  @override
  Future<Map<String, dynamic>?> fetchMeta(String photoId, String category) async {
    // Simulate async latency
    await Future<void>.delayed(Duration(milliseconds: 5));
    return responses[photoId];
  }
}

SunshineSpot _buildSpot({String? apiId, String image = 'https://images.unsplash.com/photo-12345'}) {
  return SunshineSpot(
    id: 's1',
    name: 'Spot 1',
    description: 'Nice spot',
    latitude: 45.0,
    longitude: -122.0,
    imageUrl: image,
    apiPhotoId: apiId,
    sunshineHours: 3,
    temperature: 65.0,
    weather: 'Sunny',
    rating: 4.5,
    category: 'beach',
    distance: 1.2,
  );
}

void main() {
  testWidgets('shows attribution when meta source is live', (WidgetTester tester) async {
    final fake = FakePhotoMetaService({
      'abc123': {
        'source': 'live',
        'attribution_html': 'Photo by <a href="https://unsplash.com/@photographer">Photographer</a>',
        'urls': {'regular': 'https://images.unsplash.com/photo-regular'}
      }
    });

    final spot = _buildSpot(apiId: 'abc123');

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SunshineSpotCard(
          spot: spot,
          onTap: () {},
          onFavoriteToggle: () {},
          photoMetaService: fake,
        ),
      ),
    ));

    // Let async fetch complete
    await tester.pumpAndSettle();

    final containsPhotographer = find.byWidgetPredicate((w) {
      if (w is RichText) return w.text.toPlainText().contains('Photographer');
      return false;
    });
    expect(containsPhotographer, findsOneWidget);
  });

  testWidgets('does not show attribution when meta source is demo', (WidgetTester tester) async {
    final fake = FakePhotoMetaService({
      'xyz': {
        'source': 'demo'
      }
    });

    final spot = _buildSpot(apiId: 'xyz');

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SunshineSpotCard(
          spot: spot,
          onTap: () {},
          onFavoriteToggle: () {},
          photoMetaService: fake,
        ),
      ),
    ));

    await tester.pumpAndSettle();

    final containsAttribution = find.byType(RichText);
    // There may be other RichText in the card; ensure none contain 'Photo by'
    bool found = false;
    for (final e in tester.widgetList<RichText>(containsAttribution)) {
      if (e.text.toPlainText().contains('Photo by')) {
        found = true;
        break;
      }
    }
    expect(found, isFalse);
  });
}
