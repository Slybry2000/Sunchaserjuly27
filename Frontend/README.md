# Frontend — Local dev notes

Quick notes for running the Flutter app locally against the backend.

API base URL

- The app reads the API base URL from a Dart define: `API_BASE_URL`.
- Examples (pick the one appropriate for your platform):

  - Android emulator (recommended for local Android testing):

```powershell
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

  - iOS simulator (macOS):

```bash
flutter run -d ios --dart-define=API_BASE_URL=http://localhost:8000
```

  - Web (dev): note CORS — backend must allow the dev origin or run backend with dev CORS enabled:

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

Emulator host mapping

- Android emulator: `10.0.2.2` maps to host `localhost` on your machine.
- iOS simulator: `localhost` works for host mapping.

Running tests and analyzer locally

```powershell
cd Frontend
flutter pub get
flutter analyze
flutter test
```

CI

- A GitHub Actions workflow was added at `/.github/workflows/flutter-ci.yml` to run `flutter analyze` and `flutter test` on push/PR to `master`.

Notes and troubleshooting

- If you see font warnings for missing Noto fonts, install or add a suitable font asset, or switch to `google_fonts` in the app styles (already included).
- If images fail to load from remote hosts during development, the app falls back to a local placeholder UI; consider adding a bundled placeholder image to `assets/` and updating `pubspec.yaml` if you want a nicer offline placeholder.

If you'd like, I can add the bundled placeholder image and wire it as the fallback next.
