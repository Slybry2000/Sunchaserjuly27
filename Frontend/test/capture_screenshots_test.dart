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
  testWidgets('capture screenshots (attribution, interface, integration)', (tester) async {
    final attributionSpot = SunshineSpot(
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
    final listSpots = <SunshineSpot>[
      attributionSpot,
      SunshineSpot(
        id: 'cap2',
        name: 'Shoreline Point',
        description: 'Coastal viewpoint with wide open horizon.',
        latitude: 47.7,
        longitude: -122.4,
        imageUrl: 'assets/placeholder.png',
        apiPhotoId: 'def456',
        sunshineHours: 6,
        temperature: 68,
        weather: 'Partly Cloudy',
        rating: 4.3,
        category: 'coastal',
        distance: 25.0,
        isFavorite: true,
      ),
      SunshineSpot(
        id: 'cap3',
        name: 'Forest Meadow Loop',
        description: 'Open meadow loop with filtered sunlight.',
        latitude: 47.8,
        longitude: -122.5,
        imageUrl: 'assets/placeholder.png',
        apiPhotoId: 'ghi789',
        sunshineHours: 5,
        temperature: 63,
        weather: 'Cloudy',
        rating: 4.1,
        category: 'trail',
        distance: 9.3,
        isFavorite: false,
      ),
    ];

    final attributionKey = GlobalKey();
    final interfaceKey = GlobalKey();
    final integrationKey = GlobalKey();

    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        backgroundColor: Colors.white,
        body: SingleChildScrollView(
          child: Column(
            children: [
              // Attribution example (single card)
              RepaintBoundary(
                key: attributionKey,
                child: SizedBox(
                  width: 360,
                  child: SunshineSpotCard(
                    spot: attributionSpot,
                    onTap: () {},
                    onFavoriteToggle: () {},
                    photoMetaService: _StaticMeta(),
                    photoTrackService: _NoopTrack(),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              RepaintBoundary(
                key: interfaceKey,
                child: SizedBox(
                  width: 390,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: listSpots.take(2).map((s) => Padding(
                      padding: const EdgeInsets.only(bottom:16.0),
                      child: SunshineSpotCard(
                        spot: s,
                        onTap: () {},
                        onFavoriteToggle: () {},
                        photoMetaService: _StaticMeta(),
                        photoTrackService: _NoopTrack(),
                      ),
                    )).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              // Integration view: list of multiple cards to show photo integration richness
              RepaintBoundary(
                key: integrationKey,
                child: SizedBox(
                  width: 390,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: listSpots.map((s) => Padding(
                      padding: const EdgeInsets.only(bottom:16.0),
                      child: SunshineSpotCard(
                        spot: s,
                        onTap: () {},
                        onFavoriteToggle: () {},
                        photoMetaService: _StaticMeta(),
                        photoTrackService: _NoopTrack(),
                      ),
                    )).toList(),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    ));
    await tester.pumpAndSettle();

    final screenshotDir = Directory('build/screenshots');
    if (!screenshotDir.existsSync()) {
      screenshotDir.createSync(recursive: true);
    }

    Future<void> capture(GlobalKey key, String filename) async {
      final boundary = key.currentContext!.findRenderObject() as RenderRepaintBoundary;
      final ui.Image image = await boundary.toImage(pixelRatio: 2.0);
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      final bytes = byteData!.buffer.asUint8List();
      final file = File('build/screenshots/$filename');
      await file.writeAsBytes(bytes);
    }

    await capture(attributionKey, 'attribution_example.png');
    await capture(interfaceKey, 'app_interface.png');
    await capture(integrationKey, 'photo_integration.png');
  });
}
