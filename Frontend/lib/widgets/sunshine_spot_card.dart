import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:sunshine_spotter/models/sunshine_spot.dart';

class SunshineSpotCard extends StatefulWidget {
  final SunshineSpot spot;
  final VoidCallback onTap;
  final VoidCallback onFavoriteToggle;

  const SunshineSpotCard({
    super.key,
    required this.spot,
    required this.onTap,
    required this.onFavoriteToggle,
  });

  @override
  State<SunshineSpotCard> createState() => _SunshineSpotCardState();
}

class _SunshineSpotCardState extends State<SunshineSpotCard> {
  String? _attributionHtml;
  bool _tracked = false;

  Future<void> _fetchMeta() async {
    try {
      final base = const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');
      final uri = Uri.parse(base).replace(path: '/internal/photos/meta', queryParameters: {'photo_id': widget.spot.id});
      final resp = await http.get(uri).timeout(const Duration(seconds: 3));
      if (resp.statusCode == 200) {
        final json = jsonDecode(resp.body) as Map<String, dynamic>;
        setState(() {
          _attributionHtml = json['attribution_html'] as String?;
        });
      }
    } catch (e) {
      // ignore network errors; attribution is optional
    }
  }

  Future<void> _track() async {
    if (_tracked) return;
    _tracked = true;
    try {
  final base = const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');
  final uri = Uri.parse(base).replace(path: '/internal/photos/track');
      final body = jsonEncode({'photo_id': widget.spot.id});
      await http.post(uri, headers: {'Content-Type': 'application/json'}, body: body).timeout(const Duration(seconds: 2));
    } catch (e) {
      // swallow errors
    }
  }

  @override
  void initState() {
    super.initState();
    _fetchMeta();
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
            SizedBox(
              height: 180,
              child: Stack(
                children: [
                  // Use Image.network with improved error handling
                  Positioned.fill(
                    child: Image.network(
                      spot.imageUrl,
                      fit: BoxFit.cover,
                      loadingBuilder: (context, child, loadingProgress) {
                        if (loadingProgress == null) {
                          // Image finished loading, fire tracking once
                          _track();
                          return child;
                        }
                        return Container(
                          color: Colors.grey.shade200,
                          child: const Center(
                            child: CircularProgressIndicator(),
                          ),
                        );
                      },
                      errorBuilder: (context, error, stackTrace) {
                        // Try to show a bundled placeholder asset, otherwise fallback to an icon
                        return Image.asset(
                          'assets/placeholder.png',
                          fit: BoxFit.cover,
                          errorBuilder: (ctx, err, st) => Container(
                            color: Colors.grey.shade200,
                            alignment: Alignment.center,
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.landscape,
                                  color: Colors.grey.shade500,
                                  size: 48,
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  spot.category,
                                  style: TextStyle(
                                    color: Colors.grey.shade600,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                  
                  // Gradient overlay
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.transparent,
                          Colors.black.withValues(alpha: 0.3),
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
                        color: Colors.white.withValues(alpha: 0.9),
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
                        color: Colors.white.withValues(alpha: 0.9),
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
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
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
                        style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurface.withValues(alpha: 0.8)),
                        children: _buildAttributionSpans(_attributionHtml!, theme),
                      ),
                    ),
                  ],

                  const SizedBox(height: 12),
                  
                  // Stats row
                  Row(
                    children: [
                      // Rating
                      Row(
                        children: [
                          Icon(
                            Icons.star,
                            color: Colors.amber,
                            size: 16,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            spot.rating.toString(),
                            style: theme.textTheme.labelMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                      
                      const SizedBox(width: 16),
                      
                      // Distance
                      Row(
                        children: [
                          Icon(
                            Icons.location_on,
                            color: theme.colorScheme.primary,
                            size: 16,
                          ),
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
                      
                      const Spacer(),
                      
                      // Sunshine hours
                      Row(
                        children: [
                          Icon(
                            Icons.wb_sunny_outlined,
                            color: theme.colorScheme.secondary,
                            size: 16,
                          ),
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
    // Very small helper: convert simple anchor tags to visible link text.
    // Example input: 'Photo by <a href="...">Name</a> on <a href="...">Unsplash</a>'
    try {
      final reg = RegExp(r'<a[^>]*>([^<]+)<\/a>', caseSensitive: false);
      final matches = reg.allMatches(html).toList();
      if (matches.isEmpty) return [TextSpan(text: html)];

      List<InlineSpan> spans = [];
      int last = 0;
      for (final m in matches) {
        if (m.start > last) {
          spans.add(TextSpan(text: html.substring(last, m.start)));
        }
        final linkText = m.group(1) ?? '';
        spans.add(TextSpan(text: linkText, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.primary)));
        last = m.end;
      }
      if (last < html.length) spans.add(TextSpan(text: html.substring(last)));
      return spans;
    } catch (e) {
      return [TextSpan(text: html)];
    }
  }
}