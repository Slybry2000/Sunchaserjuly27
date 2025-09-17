## Unsplash Integration Implementation

This document explains the minimal backend helpers and wiring used to satisfy
the Unsplash production checklist items (download tracking and attribution).

Files added:

- `Backend/services/unsplash_integration.py` — small helpers used by API handlers
  - `trigger_photo_download(download_location, access_key)` — calls Unsplash download endpoint
  - `build_attribution_html(photo)` — returns a compact HTML attribution snippet
- `Backend/tests/test_unsplash_integration.py` — unit tests for the helpers

How it satisfies checklist items:

- Download Tracking: call `trigger_photo_download(photo.links.download_location, ACCESS_KEY)`
  from the endpoint that returns photo metadata to the frontend, or in a background
  task when a photo is displayed. The helper attaches the required `Client-ID` header
  and returns success/failure.

- Proper Attribution: `build_attribution_html` returns the required
  "Photo by [Photographer] on Unsplash" HTML snippet with links to the
  photographer profile and the Unsplash photo page. Frontend should render
  this content visibly beneath each photo and make the links tappable.

Frontend wiring suggestion (Flutter/Dart):

1. When you obtain a photo object from the backend, show the image using
   the Unsplash `urls.regular` value and _do not_ persist the image locally
   outside of the device cache.
2. Immediately (or when the image first becomes visible) request the backend
   to trigger download tracking. Example pseudo-code:

   - Backend endpoint: `/v1/photos/track?location={download_location}`
   - Handler should call `trigger_photo_download(download_location, ACCESS_KEY)`

3. Render the attribution returned by `build_attribution_html(photo)` in the UI
   using rich text with tappable links.

Notes and recommendations:

- The `ACCESS_KEY` must be the Unsplash Client ID. Keep production keys in
  your secrets manager and only inject them into the backend environment.
- Rate limits: ensure download tracking requests are debounced for repeated
  views of the same photo by the same user to avoid unnecessary API calls.
- Visual distinction: verify your UI does not mimic Unsplash branding. The
  code here only covers tracking and attribution; unique branding is a
  frontend design task.

Next steps (optional but recommended):

- Add a small backend endpoint that accepts a photo object or download_location
  and returns the attribution snippet and a tracked flag. This centralizes
  attribution formatting and download tracking for mobile clients.
- Implement caching and debouncing so repeated views from the same session
  don't trigger the download endpoint repeatedly.
