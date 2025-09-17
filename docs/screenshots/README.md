# Screenshot Artifacts

This folder will store generated screenshots for Unsplash application submission.

Required images (generated automatically):
1. attribution_example.png – Shows attribution with clickable links.
2. app_interface.png – Main recommendation UI (distinct branding, multiple cards).
3. photo_integration.png – Rich list of varied category cards demonstrating photo enhancement.

Automation: A Flutter golden-style test (`capture_screenshots_test.dart`) renders representative widgets and saves PNG assets under `build/screenshots/`. CI job uploads them as artifacts.
