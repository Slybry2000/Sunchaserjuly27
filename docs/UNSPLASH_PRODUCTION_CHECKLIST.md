# Unsplash Production Application Checklist
*Complete checklist for Sun Chaser Unsplash API production approval*

## Pre-Application Requirements

### ✅ Technical Implementation
- [ ] **Photo Hotlinking**: All photos must hotlink to original Unsplash URLs
  - [ ] Use `photo.urls.regular` for display images
  - [ ] Use `photo.urls.small` for thumbnails
  - [ ] Never cache or store Unsplash images locally
  
 - [x] **Download Tracking**: Trigger download endpoint when users view photos
   - [x] Implement `triggerDownload()` function (backend helper added in `Backend/services/unsplash_integration.py` and unit-tested)
    - [ ] Call download endpoint when photo is displayed (frontend wiring required)
   - [x] Track each unique photo view (not duplicate views) — implemented server-side dedupe using in-process TTL cache
   - [x] Add a small backend endpoint to centralize tracking so the Client-ID is never exposed to clients (`/internal/photos/track`)
   - [x] Add integration-style tests: server-side meta endpoint + track flow added (`/internal/photos/meta` and test in `Backend/tests/test_unsplash_router.py`)
   - [x] Instrument tracking endpoint with basic metrics (success/failure counters)
  
- [ ] **Visual Distinction**: App must not resemble Unsplash
  - [ ] No Unsplash logo in app UI
  - [ ] App name cannot include "Unsplash" (❌ "Unsplasher")
  - [ ] Different color scheme from Unsplash
  - [ ] Unique app branding and layout

- [ ] **Proper Attribution**: Photographer and Unsplash must be credited
  - [ ] "Photo by [Photographer Name] on Unsplash" format
  - [ ] Photographer name links to their Unsplash profile
  - [ ] "Unsplash" text links to photo's Unsplash page
  - [ ] Attribution visible on every photo
  - [x] Server-side helper `build_attribution_html(photo)` added in `Backend/services/unsplash_integration.py` (unit-tested)
  - [ ] Frontend must render attribution visibly for each photo and ensure links are tappable

### 📱 App Information
- [ ] **Application Name**: "Sun Chaser" (confirmed distinct from Unsplash)
- [ ] **Application Description**: Clear explanation of outdoor recreation focus
- [ ] **Accurate Representation**: Description matches actual app functionality

## Application Materials

### 📝 Application Description
```
Application Name: Sun Chaser

Description: Sun Chaser is a mobile application that helps outdoor enthusiasts 
discover hiking trails, parks, lakes, and other recreational locations in the 
Pacific Northwest. The app provides weather-aware recommendations for outdoor 
activities based on user location and preferences.

We use Unsplash's API to display high-quality landscape photography that 
represents the natural beauty of recommended locations. All photos are properly 
attributed to their photographers and link back to Unsplash as required.

Key Features:
- Location-based outdoor recreation recommendations
- Weather integration for activity planning  
- High-quality location photography via Unsplash API
- Proper photographer attribution and Unsplash crediting

Expected Usage: Approximately 1,000-2,000 photo requests per day as users 
browse location recommendations. Photos are cached on device to minimize 
repeated requests for the same content.

We are committed to following all Unsplash API guidelines and providing 
proper attribution to photographers while driving traffic back to Unsplash.
```

### 📸 Required Screenshots
Create screenshots showing:

1. **Photo Attribution Example**
   - Screenshot showing "Photo by [Name] on Unsplash" 
   - Demonstrate clickable links to photographer and Unsplash
   - Show attribution is clearly visible and properly formatted

2. **App Interface**
   - Main app screen showing location recommendations
   - Demonstrate visual distinction from Unsplash interface
   - Show app branding and unique design elements

3. **Photo Integration**
   - Location cards with Unsplash photos
   - Show how photos enhance location discovery experience
   - Demonstrate photos are hotlinked (not locally stored)

### 🔗 Implementation Examples

**Required Code Implementation:**
```dart
// 1. Photo Hotlinking - Use Unsplash URLs directly
CachedNetworkImage(
  imageUrl: unsplashPhoto.urls.regular, // Direct Unsplash URL
  // Never download or cache the actual image file
)

// 2. Download Tracking - Required for every photo view
Future<void> trackPhotoUsage(UnsplashPhoto photo) async {
  final response = await http.get(
    Uri.parse(photo.links.downloadLocation),
    headers: {'Authorization': 'Client-ID $accessKey'},
  );
}

// 3. Proper Attribution - Required on every photo
Widget buildAttribution(UnsplashPhoto photo) {
  return Text.rich(
    TextSpan(
      children: [
        TextSpan(text: 'Photo by '),
        TextSpan(
          text: photo.user.name,
          style: TextStyle(decoration: TextDecoration.underline),
          recognizer: TapGestureRecognizer()
            ..onTap = () => launchUrl(photo.user.links.html),
        ),
        TextSpan(text: ' on '),
        TextSpan(
          text: 'Unsplash',
          style: TextStyle(decoration: TextDecoration.underline),
          recognizer: TapGestureRecognizer()
            ..onTap = () => launchUrl(photo.links.html),
        ),
      ],
    ),
  );
}
```

## Pre-Submission Checklist

### 🧪 Testing Requirements
- [ ] Test photo hotlinking works correctly
 - [ ] Verify download tracking is called for each photo view
   - [x] Backend unit tests added for the helper (see `Backend/tests/test_unsplash_integration.py`)
   - [ ] Add an integration test that simulates a frontend-visible render triggering a backend track call
 - [x] Confirm attribution links work and open correct pages (helper returns correct links; frontend rendering still required)
- [ ] Test app functionality without Unsplash branding
- [ ] Validate photo search returns relevant results
 - [ ] Frontend wiring: implement visible-once tracking and render attribution (example doc added; implementation required in frontend app)

### 📋 Documentation Review  
- [ ] Review Unsplash API Guidelines in full
- [ ] Confirm app meets all technical requirements
- [ ] Verify attribution implementation matches guidelines
- [ ] Check that app description is accurate and complete

### Implementation notes / status
- Backend helpers added:
  - `Backend/services/unsplash_integration.py` — trigger tracking + build attribution HTML
  - `Backend/tests/test_unsplash_integration.py` — unit tests (3 passing)
 - Backend routes added:
   - `POST /internal/photos/track` — deduped tracking endpoint (see `Backend/routers/unsplash.py`)
   - `GET /internal/photos/meta` — server-side metadata + attribution helper for frontend (see `Backend/routers/unsplash.py`)
 - Integration-style test added: `Backend/tests/test_unsplash_router.py` includes a meta -> track flow test and TTL expiry test (all passing)
- Docs added: `docs/UNSPLASH_IMPLEMENTATION.md` with wiring suggestions for frontend/backend.
 - Frontend example doc added: `docs/UNSPLASH_FRONTEND_EXAMPLE.md` (contains Flutter/Dart wiring sample and screenshot guidance)
 - API README added: `docs/UNSPLASH_API_README.md` (endpoints, env vars, examples)
 - PR summary added: `docs/UNSPLASH_PR_SUMMARY.md` (changed files, test commands, reviewer checklist)
 - Local tests: all new backend tests passing locally (see `Backend/tests/*`)

### PR and CI steps (new tasks)
- [ ] Prepare a PR branch and include this checklist as part of the PR description
- [ ] Branch created locally: `feature/unsplash-tracking` (will be created and committed locally)
- [ ] Add a CI job to run `pytest` for `Backend/tests/*` and fail fast on regressions
- [ ] Add a smoke job that runs the FastAPI app and calls `/internal/photos/meta` and `/internal/photos/track` (integration smoke)
- [ ] Add a secret rotation note: ensure `UNSPLASH_CLIENT_ID` is stored in the environment/secrets manager and not in repo

### Frontend / release tasks (new)
- [ ] Implement frontend wiring per `docs/UNSPLASH_FRONTEND_EXAMPLE.md` in the Flutter app and capture the 3 required screenshots
- [ ] Add a CI job (or manual job) to verify screenshot generation and attach them to the PR
- [ ] Security review: confirm no Client-ID or secrets are present in frontend bundles

### Release readiness checklist (new)
- [ ] All tests passing in CI (unit + integration smoke)
- [ ] Screenshots attached to PR demonstrating attribution and UI
- [ ] Secrets provisioned in production/staging
- [ ] Monitoring (metrics) visible in staging dashboards

### New tasks discovered (recommended ordering)
1. Add a backend route (POST `/v1/photos/track`) that accepts a photo id or `download_location` and calls `trigger_photo_download` server-side. This centralizes Client-ID usage and avoids exposing it to clients.
2. Implement session-level debouncing / dedupe for track calls to avoid duplicate tracking for the same photo within short time windows.
3. Add integration tests that exercise the tracking endpoint together with a small frontend simulator (or headless Flutter integration test) to show download tracking fires only on first visible render.
  - a. Completed a server-side integration-style test; next is a headless frontend/integration test or actual frontend implementation.
4. Add frontend wiring and screenshots:
  - a. Show the frontend using `photo.urls.regular` for images (hotlinking)
  - b. Show the frontend calling the backend track endpoint when the photo first becomes visible
  - c. Take required screenshots for the Unsplash submission (attribution visible, tappable links, app UI distinct from Unsplash)
  - d. Example wiring doc added in `docs/UNSPLASH_FRONTEND_EXAMPLE.md` to guide implementation and screenshots
    - e. API README added in `docs/UNSPLASH_API_README.md` to document endpoints, env vars, and examples
5. Secrets and deployment:
  - a. Ensure the Unsplash Client-ID is injected server-side from a secrets manager or environment variable (do not commit keys)
  - b. After production approval, swap to production API keys and monitor rate limits
6. Observability / QA:
  - a. Instrument tracking endpoint with metrics (success/fail counts, latency)
  - b. Add alerts for unusual failure rates or throttling responses from Unsplash

If you'd like, I can implement task 1 (backend route + small in-memory dedupe) next and add the integration test.

### 🎯 Quality Assurance
- [ ] App provides value beyond just displaying Unsplash photos
- [ ] Photos enhance the core outdoor recreation functionality
- [ ] Attribution is prominent and properly formatted
- [ ] App design is clearly distinct from Unsplash interface

## Application Submission

### 📤 Submission Process
1. **Complete Implementation**: Ensure all technical requirements are met
2. **Gather Screenshots**: Take screenshots demonstrating proper attribution
3. **Write Description**: Use the approved application description above
4. **Submit Application**: Apply through Unsplash Developer Portal
5. **Respond to Feedback**: Address any review comments promptly

### ⏱️ Timeline Expectations
- **Review Time**: Typically 1-2 weeks for application review
- **Response Time**: Respond to any feedback within 2-3 business days
- **Implementation**: Additional changes may require 1-2 weeks

### 🎯 Success Criteria
- **Approval**: Gain access to 5,000 requests/hour production rate limits
- **Compliance**: Meet all Unsplash attribution and technical requirements
- **Quality**: Professional integration that enhances user experience

## Post-Approval Steps

### 🚀 Production Deployment
- [ ] Update to production API keys
- [ ] Monitor rate limit usage
- [ ] Implement usage analytics
- [ ] Set up photo performance monitoring

### 📊 Ongoing Compliance
- [ ] Maintain proper attribution on all photos
- [ ] Continue download tracking for all photo views
- [ ] Regular review of Unsplash API guidelines
- [ ] Monitor photo relevance and quality

---

**Status**: Ready for implementation and application
**Timeline**: 2-3 weeks for full implementation and approval
**Priority**: High - Essential for production-quality photo experience
