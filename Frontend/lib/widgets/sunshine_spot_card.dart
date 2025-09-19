import 'package:flutter/material.dart';
import 'package:sunshine_spotter/models/sunshine_spot.dart';
import 'package:sunshine_spotter/services/location_image_service.dart';
import 'package:sunshine_spotter/services/photo_meta_service.dart';
import 'package:sunshine_spotter/services/photo_track_service.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/gestures.dart';
import 'package:visibility_detector/visibility_detector.dart';

class SunshineSpotCard extends StatefulWidget {
  final SunshineSpot spot;
  final VoidCallback onTap;
  final VoidCallback onFavoriteToggle;
  // Optional initial attribution HTML. Public API that allows callers (and
  // tests) to provide pre-fetched attribution without triggering a network
  // request. This is intentionally a public, read-only parameter to make
  // testing seams explicit while keeping production behavior unchanged.
  final String? initialAttributionHtml;
  // Optional injectable service used to fetch photo meta; tests can inject
  // a mock implementation.
  final PhotoMetaService? photoMetaService;
  // Optional injectable service used to send tracking POSTs; tests can inject
  // a fake implementation to assert calls.
  final PhotoTrackService? photoTrackService;

  const SunshineSpotCard({
    super.key,
    required this.spot,
    required this.onTap,
    required this.onFavoriteToggle,
  this.initialAttributionHtml,
  this.photoMetaService,
  this.photoTrackService,
  });

  @override
  State<SunshineSpotCard> createState() => _SunshineSpotCardState();
}

class _SunshineSpotCardState extends State<SunshineSpotCard> {
  String? _attributionHtml;
  bool _tracked = false;
  bool _loggedImage = false; // prevent log spam
  // Keep recognizers so we can dispose them when the widget is removed
  // or when attribution is rebuilt to avoid memory leaks.
  List<TapGestureRecognizer> _attributionRecognizers = [];
  List<Map<String, String>>? _fallbackPool; // ordered pool for this category (entries with url + apiId)
  int _fallbackIndex = 0;
  late String _currentImageUrl; // mutable current image (for fallback rotation)

  Future<void> _fetchMeta() async {
    try {
  // Prefer API photo id directly from the spot if present
  final metaService = widget.photoMetaService ?? HttpPhotoMetaService();
  if ((widget.spot.apiPhotoId ?? '').isNotEmpty) {
    final json = await metaService.fetchMeta(widget.spot.apiPhotoId!, widget.spot.category);
    if (json != null) {
      final source = (json['source'] as String?) ?? 'demo';
      if (source == 'live') {
        final urls = (json['urls'] as Map?)?.cast<String, dynamic>();
        final newUrl = urls != null ? (urls['regular'] as String?) : null;
        setState(() {
          _attributionHtml = json['attribution_html'] as String?;
          if (newUrl != null && newUrl.isNotEmpty && newUrl != _currentImageUrl) {
            _currentImageUrl = newUrl;
            _tracked = false; _loggedImage = false;
          }
        });
  // Track immediately; card is visible already when meta arrives.
  _track();
        return;
      }
    }
  }
  // Fallback: Only attempt Unsplash attribution if the current image is an Unsplash URL
  if (!_currentImageUrl.contains('images.unsplash.com')) return;
  // Prefer apiId when available from our pools
  String? photoId;
  try {
    final pool = LocationImageService.getCategoryImagePool(widget.spot.category);
  final match = pool.firstWhere((e) => (e['url'] ?? '') == _currentImageUrl, orElse: () => <String, String>{});
  if (match.isNotEmpty && (match['apiId'] ?? '').isNotEmpty) {
      photoId = match['apiId'];
    }
  } catch (_) {
    // ignore
  }
  photoId ??= _deriveUnsplashPhotoId(_currentImageUrl);
  // Heuristic: CDN filenames like 'photo-1508609349937-...' are not real API IDs.
  // Skip meta fetch for those to avoid showing placeholder "Demo Photographer".
  if (photoId.startsWith('photo-')) return;
  final json = await metaService.fetchMeta(photoId, widget.spot.category);
      if (json != null) {
        final source = (json['source'] as String?) ?? 'demo';
        if (source == 'live') {
          final urls = (json['urls'] as Map?)?.cast<String, dynamic>();
          final newUrl = urls != null ? (urls['regular'] as String?) : null;
          setState(() {
            _attributionHtml = json['attribution_html'] as String?;
            if (newUrl != null && newUrl.isNotEmpty && newUrl != _currentImageUrl) {
              _currentImageUrl = newUrl;
              _tracked = false; // allow tracking image switch
              _loggedImage = false;
            }
          });
          // Invoke tracking for the updated image immediately.
          _track();
        } else {
          // Demo fallback: keep original image to avoid 404 placeholders
          setState(() {
            _attributionHtml = null; // don't show demo attribution
          });
        }
      }
    } catch (e) {
      debugPrint('meta fetch exception: $e');
      // ignore network errors; attribution is optional
    }
  }

  Future<void> _track() async {
    if (_tracked) return;
    try {
      final trackService = widget.photoTrackService ?? HttpPhotoTrackService();
      // Track by direct API id when available
      if ((widget.spot.apiPhotoId ?? '').isNotEmpty) {
        final ok = await trackService.trackPhoto(widget.spot.apiPhotoId!);
        if (ok) _tracked = true;
        return;
      }
      if (!_currentImageUrl.contains('images.unsplash.com')) return;
      String? photoId;
      try {
        final pool = LocationImageService.getCategoryImagePool(widget.spot.category);
        final match = pool.firstWhere((e) => (e['url'] ?? '') == _currentImageUrl, orElse: () => <String, String>{});
        if (match.isNotEmpty && (match['apiId'] ?? '').isNotEmpty) {
          photoId = match['apiId'];
        }
      } catch (_) {}
      photoId ??= _deriveUnsplashPhotoId(_currentImageUrl);
      final ok = await trackService.trackPhoto(photoId);
      if (ok) _tracked = true;
    } catch (e) {
      debugPrint('track exception: $e');
    }
  }

  @override
  void initState() {
    super.initState();
  _currentImageUrl = widget.spot.imageUrl;
    // Prepare pool for automatic 404 fallback (only for Unsplash URLs)
    if (widget.spot.imageUrl.startsWith('http')) {
      // keep growable so we can iterate/rotate without recreating lists
      _fallbackPool = LocationImageService.getCategoryImagePool(widget.spot.category)
        .where((u) => (u['url'] ?? '') != widget.spot.imageUrl) // exclude current
        .toList(growable: true);
      // Seed the fallback index deterministically per card so multiple cards
      // in the same category don't all pick the first fallback image.
      if (_fallbackPool!.isNotEmpty) {
        final hash = widget.spot.id.codeUnits.fold<int>(0, (a, c) => (a * 31 + c) & 0x7fffffff);
        _fallbackIndex = hash % _fallbackPool!.length;
      }
    }
    // If an initial attribution HTML was provided by the caller, prefer that
    // (useful for tests or if the caller already fetched meta). Otherwise
    // fetch attribution after pool is ready so we can prefer apiId from the
    // pool.
    if (widget.initialAttributionHtml != null) {
      _attributionHtml = widget.initialAttributionHtml;
    } else {
      _fetchMeta();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final spot = widget.spot;
    
  return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
    onTap: widget.onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image with favorite button overlay
            // VisibilityDetector wraps the image stack to trigger tracking only when
            // the card is actually visible (>=40% of its area) to approximate a user view.
            VisibilityDetector(
              key: Key('spot-visible-${spot.id}'),
              onVisibilityChanged: (info) {
                if (info.visibleFraction >= 0.4) {
                  _track();
                }
              },
              child: SizedBox(
                height: 180,
                child: Stack(
                  children: [
                    // Use Image.network with improved error handling
                    Positioned.fill(child: _buildResilientImage(spot)),
                    // Gradient overlay
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.transparent,
                            Colors.black.withAlpha((0.3 * 255).round()),
                          ],
                        ),
                      ),
                    ),
                    // Favorite button
                    Positioned(
                      top: 12,
                      right: 12,
                        child: Container(
                        decoration: BoxDecoration(
                          color: Colors.white.withAlpha((0.9 * 255).round()),
                          shape: BoxShape.circle,
                        ),
                        child: IconButton(
                          onPressed: widget.onFavoriteToggle,
                          icon: Icon(
                            spot.isFavorite ? Icons.favorite : Icons.favorite_border,
                            color: spot.isFavorite ? Colors.red : Colors.grey[600],
                            size: 22,
                          ),
                        ),
                      ),
                    ),
                    // Weather info overlay
                    Positioned(
                      bottom: 12,
                      right: 12,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white.withAlpha((0.9 * 255).round()),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.wb_sunny,
                              color: theme.colorScheme.primary,
                              size: 16,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '${spot.temperature.toInt()}°F',
                              style: theme.textTheme.labelMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // Content
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title and category
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          spot.name,
                          style: theme.textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.primaryContainer,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          spot.category,
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: theme.colorScheme.onPrimaryContainer,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 8),
                  
                  // Description
                  Text(
                    spot.description,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withAlpha((0.8 * 255).round()),
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  
                  // Attribution (fetched from backend, optional)
                  if (_attributionHtml != null) ...[
                    const SizedBox(height: 8),
                    // Simple rendering: strip basic HTML and show as tappable link if present
                    RichText(
                      text: TextSpan(
                        style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurface.withAlpha((0.8 * 255).round())),
                        children: _buildAttributionSpans(_attributionHtml!, theme),
                      ),
                    ),
                  ],

                  const SizedBox(height: 12),
                  
                  // Stats row
                  // Stats row converted to Wrap to avoid RenderFlex overflow on narrow widths
                  Wrap(
                    spacing: 16,
                    runSpacing: 8,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.star, color: Colors.amber, size: 16),
                          const SizedBox(width: 4),
                          Text(
                            spot.rating.toString(),
                            style: theme.textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.location_on, color: theme.colorScheme.primary, size: 16),
                          const SizedBox(width: 4),
                          Text(
                            '${spot.distance.toStringAsFixed(1)} mi',
                            style: theme.textTheme.labelMedium?.copyWith(
                              color: theme.colorScheme.primary,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.wb_sunny_outlined, color: theme.colorScheme.secondary, size: 16),
                          const SizedBox(width: 4),
                          Text(
                            '${spot.sunshineHours}h',
                            style: theme.textTheme.labelMedium?.copyWith(
                              color: theme.colorScheme.secondary,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<InlineSpan> _buildAttributionSpans(String html, ThemeData theme) {
    // Convert simple anchor tags to tappable links using url_launcher.
    // Example: 'Photo by <a href="...">Name</a> on <a href="...">Unsplash</a>'
    try {
      // Dispose previous recognizers before creating new ones.
      for (final r in _attributionRecognizers) {
        r.dispose();
      }
      _attributionRecognizers = [];

      final reg = RegExp(r'''<a[^>]*href=["']([^"']+|[^']+)["'][^>]*>([^<]+)<\/a>''', caseSensitive: false);
      final matches = reg.allMatches(html).toList();
      if (matches.isEmpty) return [TextSpan(text: html)];

      List<InlineSpan> spans = [];
      int last = 0;
      for (final m in matches) {
        if (m.start > last) {
          spans.add(TextSpan(text: html.substring(last, m.start)));
        }
        final href = m.group(1) ?? '';
        final linkText = m.group(2) ?? href;
        final recognizer = TapGestureRecognizer()
          ..onTap = () async {
            final uri = Uri.tryParse(href);
            if (uri != null) {
              await launchUrl(uri, mode: LaunchMode.externalApplication);
            }
          };
        _attributionRecognizers.add(recognizer);
        spans.add(TextSpan(
          text: linkText,
          style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.primary, decoration: TextDecoration.underline),
          recognizer: recognizer,
        ));
        last = m.end;
      }
      if (last < html.length) spans.add(TextSpan(text: html.substring(last)));
      return spans;
    } catch (e) {
      return [TextSpan(text: html)];
    }
  }

  /// Builds an image widget that can handle either network or asset paths and logs failures.
  Widget _buildResilientImage(SunshineSpot spot) {
    final url = _currentImageUrl.trim();
    final bool isNetwork = url.startsWith('http');

    Widget buildPlaceholder([String? reason]) {
      return Stack(
        fit: StackFit.expand,
        children: [
          // Attempt placeholder asset
          Image.asset(
            'assets/placeholder.png',
            fit: BoxFit.cover,
            errorBuilder: (ctx, err, st) {
              return Container(
                color: Colors.grey.shade200,
                alignment: Alignment.center,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.landscape, size: 48, color: Colors.grey),
                    const SizedBox(height: 8),
                    Text(
                      spot.category,
                      style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                    ),
                    if (reason != null) ...[
                      const SizedBox(height: 6),
                      Text(
                        reason,
                        style: TextStyle(color: Colors.grey.shade500, fontSize: 10),
                        textAlign: TextAlign.center,
                      )
                    ],
                  ],
                ),
              );
            },
          ),
        ],
      );
    }

    if (!isNetwork) {
      // Treat as asset path
      return Image.asset(
        url,
        fit: BoxFit.cover,
        errorBuilder: (c, e, st) {
          debugPrint('Image asset load failed: $url error=$e');
          return buildPlaceholder('asset missing');
        },
      );
    }

    return Image.network(
      url,
      fit: BoxFit.cover,
      loadingBuilder: (context, child, loadingProgress) {
        if (!_loggedImage) {
          debugPrint('Loading image for spot ${spot.id} category=${spot.category} url=$url');
          _loggedImage = true;
        }
        if (loadingProgress == null) {
          return child; // tracking occurs via VisibilityDetector
        }
        return Container(
          color: Colors.grey.shade200,
          child: const Center(child: CircularProgressIndicator()),
        );
      },
      errorBuilder: (context, error, stackTrace) {
        debugPrint('Image network load failed for spot ${spot.id}: $url error=$error');
        final errorString = error.toString();
        final is404 = errorString.contains('404') || errorString.contains('Not Found');
          if (is404 && _fallbackPool != null && _fallbackPool!.isNotEmpty && _fallbackIndex < _fallbackPool!.length) {
          final nextEntry = _fallbackPool![_fallbackIndex++];
          final nextUrl = nextEntry['url'] ?? nextEntry.values.first;
          final nextApi = nextEntry['apiId'] ?? '';
          debugPrint('Attempting fallback image for spot ${spot.id}: $nextUrl (apiId=$nextApi)');
          WidgetsBinding.instance.addPostFrameCallback((_) {
            setState(() {
              _currentImageUrl = nextUrl;
              _tracked = false; // allow tracking again for new image
              _attributionHtml = null; // new image -> refetch attribution
              _loggedImage = false; // log new image load
            });
            _fetchMeta();
          });
          return Container(color: Colors.grey.shade200);
        }
        return buildPlaceholder('image unavailable');
      },
    );
  }

  String _deriveUnsplashPhotoId(String url) {
    // Extract last path segment (Unsplash CDN filename). Note: This is NOT the
    // public Unsplash API photo ID unless it lacks the 'photo-' prefix and is a
    // short base62-like string. We use this only to detect when we *should not*
    // attempt a metadata fetch (i.e., when it starts with 'photo-').
    try {
      final pathSeg = Uri.parse(url).pathSegments.last;
      return pathSeg.split('?').first;
    } catch (_) {
      return widget.spot.id; // fallback
    }
  }

  @override
  void dispose() {
    for (final r in _attributionRecognizers) {
      r.dispose();
    }
    _attributionRecognizers = [];
    super.dispose();
  }
}