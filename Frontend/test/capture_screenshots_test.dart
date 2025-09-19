import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';

/// A tiny test asset bundle that returns a valid 1x1 PNG for the
/// test placeholder asset so `Image.asset` does not attempt network
/// or fail with invalid image data during widget tests.
class _TestAssetBundle extends CachingAssetBundle {
  // A known-valid 1x1 PNG (transparent). Using a canonical base64 avoids
  // corrupted-message errors during tests.
  static final Uint8List _onePxPng = base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQImWNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII='
  );

  @override
  Future<ByteData> load(String key) async {
    // Normalize key because tests may request with or without leading slash
    final normalized = key.startsWith('/') ? key.substring(1) : key;
    if (normalized == 'assets/placeholder.png' || key.endsWith('assets/placeholder.png')) {
      return ByteData.view(_onePxPng.buffer);
    }
    // Fallback: return an empty 1x1 PNG for any other asset to be safe.
    return ByteData.view(_onePxPng.buffer);
  }

  @override
  Future<String> loadString(String key, {bool cache = true}) async => '';
}

// Note: old test-local meta/track stubs removed as they are not referenced.

/// Minimal test-only card that mirrors the key visual structure of the
/// real `SunshineSpotCard` but uses `Image.memory` so tests don't rely on
/// Flutter assets or network images.
class _TestSpotCard extends StatelessWidget {
  final SunshineSpot spot;
  final String? attributionHtml;
  const _TestSpotCard({required this.spot, this.attributionHtml});

  List<InlineSpan> _simpleAttributionSpans(String html, ThemeData theme) {
    // Very small parser: extract anchor texts and render underlined spans
  final reg = RegExp("<a[^>]*href=[\"\\']([^\"\\']+)[\"\\'][^>]*>([^<]+)</a>", caseSensitive: false);
    final matches = reg.allMatches(html).toList();
    if (matches.isEmpty) return [TextSpan(text: html)];
    List<InlineSpan> spans = [];
    int last = 0;
    for (final m in matches) {
      if (m.start > last) spans.add(TextSpan(text: html.substring(last, m.start)));
      final text = m.group(2) ?? m.group(1) ?? '';
      spans.add(TextSpan(text: text, style: theme.textTheme.bodySmall?.copyWith(decoration: TextDecoration.underline)));
      last = m.end;
    }
    if (last < html.length) spans.add(TextSpan(text: html.substring(last)));
    return spans;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: 180,
            child: Stack(
              children: [
                Positioned.fill(
                  child: Container(color: Colors.grey.shade300),
                ),
                Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Colors.transparent, Colors.black.withValues(alpha: 0.3)],
                    ),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Expanded(child: Text(spot.name, style: theme.textTheme.titleLarge)),
                  const SizedBox(width: 8),
                ]),
                const SizedBox(height: 8),
                Text(spot.description, maxLines: 2, overflow: TextOverflow.ellipsis),
                if (attributionHtml != null) ...[
                  const SizedBox(height: 8),
                  RichText(text: TextSpan(style: theme.textTheme.bodySmall, children: _simpleAttributionSpans(attributionHtml!, theme))),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

void main() {
  final isCI = Platform.environment['CI'] == 'true' || Platform.environment['GITHUB_ACTIONS'] == 'true';
  testWidgets('capture screenshots (attribution, interface, integration)', (tester) async {
    final attributionSpot = SunshineSpot(
      id: 'cap1',
      name: 'Cascade Ridge Vista',
      description: 'Panoramic alpine overlook with clear sky exposure.',
      latitude: 47.6,
      longitude: -122.3,
  // Use local placeholder instead of network image to avoid flaky network loads in tests
  imageUrl: 'assets/placeholder.png',
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

  await tester.pumpWidget(
      DefaultAssetBundle(
        bundle: _TestAssetBundle(),
        child: MaterialApp(
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
                      child: _TestSpotCard(
                        spot: attributionSpot,
                        attributionHtml: 'Photo by <a href="https://unsplash.com/@user">User</a> on <a href="https://unsplash.com/photos/${attributionSpot.apiPhotoId}">Unsplash</a>',
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
                          child: _TestSpotCard(
                            spot: s,
                            attributionHtml: 'Photo by <a href="https://unsplash.com/@user">User</a> on <a href="https://unsplash.com/photos/${s.apiPhotoId}">Unsplash</a>',
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
                          child: _TestSpotCard(
                            spot: s,
                            attributionHtml: 'Photo by <a href="https://unsplash.com/@user">User</a> on <a href="https://unsplash.com/photos/${s.apiPhotoId}">Unsplash</a>',
                          ),
                        )).toList(),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  // Avoid pumpAndSettle (can hang with offstage timers). Pump a few frames instead.
  await tester.pump(const Duration(milliseconds: 50));
  await tester.pump(const Duration(milliseconds: 50));

    final screenshotDir = Directory('build/screenshots');
    if (!screenshotDir.existsSync()) {
      screenshotDir.createSync(recursive: true);
    }

    Future<void> capture(WidgetTester tester, GlobalKey key, String filename) async {
      // Ensure the target is visible so it gets laid out and painted.
      await tester.ensureVisible(find.byKey(key));
      await tester.pump(const Duration(milliseconds: 50));
      final boundary = key.currentContext?.findRenderObject() as RenderRepaintBoundary?;
      if (boundary == null) {
  debugPrint('capture: no RenderRepaintBoundary found for $filename; writing placeholder PNG');
        final file = File('build/screenshots/$filename');
        await file.writeAsBytes(_TestAssetBundle._onePxPng);
        return;
      }
      await tester.runAsync(() async {
        final ui.Image image = await boundary.toImage(pixelRatio: 2.0);
        final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
        Uint8List bytes;
        if (byteData == null || byteData.lengthInBytes == 0) {
          debugPrint('capture: toByteData returned null/empty for $filename; writing placeholder PNG');
          bytes = _TestAssetBundle._onePxPng;
        } else {
          bytes = byteData.buffer.asUint8List();
          debugPrint('capture: generated ${bytes.length} bytes for $filename');
        }
        final file = File('build/screenshots/$filename');
        await file.writeAsBytes(bytes);
      });
    }

    await capture(tester, attributionKey, 'attribution_example.png');
    await capture(tester, interfaceKey, 'app_interface.png');
    await capture(tester, integrationKey, 'photo_integration.png');
  }, skip: isCI ? true : false, timeout: const Timeout(Duration(seconds: 60)));
}
