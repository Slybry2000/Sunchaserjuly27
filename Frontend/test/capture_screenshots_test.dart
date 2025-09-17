import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:flutter/rendering.dart';
import 'package:sunshine_spotter/widgets/sunshine_spot_card.dart';

import 'package:sunshine_spotter/services/photo_meta_service.dart';
import 'package:sunshine_spotter/services/photo_track_service.dart';

class _StaticMeta implements PhotoMetaService {
  @override
  Future<Map<String, dynamic>?> fetchMeta(String photoId, String category) async {
    return {
      'attribution_html': 'Photo by <a href="https://unsplash.com/@user">User</a> on <a href="https://unsplash.com/photos/$photoId">Unsplash</a>',
      'urls': {'regular': 'https://images.unsplash.com/photo-abc123'},
      'source': 'live'
    };
  }
}

class _NoopTrack implements PhotoTrackService {
  @override
  Future<bool> trackPhoto(String photoId) async => true;
}

void main() {
  testWidgets('capture screenshots', (tester) async {
    final spot = SunshineSpot(
      id: 'cap1',
      name: 'Cascade Ridge Vista',
      description: 'Panoramic alpine overlook with clear sky exposure.',
      latitude: 47.6,
      longitude: -122.3,
      imageUrl: 'https://images.unsplash.com/photo-abc123',
      apiPhotoId: 'abc123',
      sunshineHours: 8,
      temperature: 72,
      weather: 'Sunny',
      rating: 4.7,
      category: 'hiking',
      distance: 12.4,
      isFavorite: false,
    );

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        backgroundColor: Colors.white,
        body: Center(
          child: SizedBox(
            width: 360,
            child: SunshineSpotCard(
              spot: spot,
              onTap: () {},
              onFavoriteToggle: () {},
              photoMetaService: _StaticMeta(),
              photoTrackService: _NoopTrack(),
            ),
          ),
        ),
      ),
    ));
    await tester.pumpAndSettle();

    final screenshotDir = Directory('build/screenshots');
    if (!screenshotDir.existsSync()) {
      screenshotDir.createSync(recursive: true);
    }
  // Wrap target widget in RepaintBoundary to capture.
  final cardFinder = find.byType(SunshineSpotCard);
  expect(cardFinder, findsOneWidget);
  final element = tester.element(cardFinder);
  final renderObject = element.renderObject;
  expect(renderObject, isNotNull);
  final boundary = renderObject as RenderRepaintBoundary?;
  expect(boundary, isNotNull);
  final ui.Image image = await boundary!.toImage(pixelRatio: 2.0);
  final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
  final bytes = byteData!.buffer.asUint8List();
  final file = File('build/screenshots/attribution_example.png');
  await file.writeAsBytes(bytes);
  });
}
