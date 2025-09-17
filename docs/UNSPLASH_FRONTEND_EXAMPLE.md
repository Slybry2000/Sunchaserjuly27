# Frontend Wiring Example (Flutter)

This file shows a minimal, recommended pattern for the Flutter frontend to
integrate with the backend tracking and attribution helpers we added.

Purpose:
- Use server-provided `urls.regular` for hotlinking images
- Render attribution returned by the backend (`attribution_html`) visibly
- Call the backend tracking endpoint once when an image first becomes visible

Notes: adapt to your app architecture (Bloc/Provider/GetX) but keep the flow:
1. Request `/internal/photos/meta?photo_id=...` from the backend
2. Render the image using the returned `urls.regular`
3. Render the returned `attribution_html` (or parse into native widgets)
4. Call POST `/internal/photos/track` with `download_location` once when image appears

Example (pseudo-Flutter/Dart):

```dart
// fetch meta
final metaResp = await http.get(Uri.parse('$API_BASE/internal/photos/meta?photo_id=$id'));
final meta = jsonDecode(metaResp.body);
final imageUrl = meta['urls']['regular'];
final downloadLocation = meta['links']['download_location'];
final attributionHtml = meta['attribution_html'];

// Widget: display image and attribution; call track when visible
class PhotoCard extends StatefulWidget {
  final String imageUrl;
  final String downloadLocation;
  final String attributionHtml;

  PhotoCard({required this.imageUrl, required this.downloadLocation, required this.attributionHtml});

  @override
  _PhotoCardState createState() => _PhotoCardState();
}

class _PhotoCardState extends State<PhotoCard> {
  bool _tracked = false;

  void _maybeTrack() async {
    if (_tracked) return;
    // Call your backend track endpoint
    await http.post(
      Uri.parse('$API_BASE/internal/photos/track'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'download_location': widget.downloadLocation}),
    );
    setState(() => _tracked = true);
  }

  @override
  Widget build(BuildContext context) {
    // Use visibility detection (e.g., VisibilityDetector package or
    // on-screen-detection in your list view) to call _maybeTrack when widget
    // first becomes visible.
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        CachedNetworkImage(imageUrl: widget.imageUrl),
        // Render attribution: you can parse the HTML or display safely as text
        Text(parseAttribution(widget.attributionHtml)),
      ],
    );
  }
}

String parseAttribution(String html) {
  // Minimal parse: extract visible text. For production, convert links to
  // tappable widgets that open the URLs.
  return html.replaceAll(RegExp(r'<[^>]*>'), '');
}
```

Screenshot guidance (for Unsplash submission):
- Photo Attribution Example: show the photo with the visible "Photo by X on Unsplash" text. Tap/click behavior should open photographer page and Unsplash page — capture a screenshot showing the tap state or open link destination.
- App Interface: main screen showing location cards with images and attribution. Emphasize unique branding and color scheme (avoid Unsplash look).
- Photo Integration: show location cards including the Unsplash image loaded via `urls.regular` and the visible attribution.

Security & keys
- Backend keeps `UNSPLASH_CLIENT_ID` secret. Do not store the client ID in the app or repo.

Performance
- Debounce track calls in the frontend as well (avoid calling backend repeatedly while user scrolls rapidly). The backend will dedupe requests server-side.

Next: implement this pattern in your frontend app and capture the required screenshots.
