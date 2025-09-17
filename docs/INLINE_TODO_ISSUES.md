# Inline TODOs converted to tracked issues

This file collects inline `TODO` comments found across the codebase and assigns a stable issue ID for tracking. Each code TODO was replaced with a short pointer comment referencing the issue ID. Use the issue IDs to locate, prioritize, and resolve items.

Format: TODO-<n>: short title — status — details & location

TODO-1: Make attribution links tappable — Not Done — Frontend needs `url_launcher` to make attribution links tappable. See `Frontend/lib/widgets/*` and `docs/UNSPLASH_PRODUCTION_CHECKLIST.md`.

TODO-2: Check asset exists in bundle — Not Done — `Frontend/lib/services/location_image_service.dart` contains a TODO to verify bundled assets before use.

TODO-3: Remove fallback section in next cleanup — Not Done — `Frontend/lib/services/data_service.dart` has a code TODO indicating planned removal of legacy fallback code.

TODO-4: Implement HomePage wiring — Not Done — `Frontend/lib/main.dart` comment: `// TODO(agent): please implement.`

TODO-5: Android app id and signing config — Not Done — `Frontend/android/app/build.gradle` TODOs to set applicationId and signing config before release builds.

TODO-6: Frontend model numeric casts review — Not Done — `Frontend/lib/models/recommend_response.dart` has numeric casting that should be reviewed/refactored for null-safety and parse errors.

TODO-7: Ensure screenshots captured for Unsplash submission — Not Done — See `docs/UNSPLASH_PRODUCTION_CHECKLIST.md` and `docs/TODO_CONSOLIDATED.md`.

---

If you'd like, I can create GitHub Issues for each TODO and/or start implementing the high-priority ones (TODO-1/TODO-7). Which would you prefer?
