# Builds the Flutter web app with production API base URL.
# Usage:
#   .\scripts\build_web_prod.ps1 -ApiBaseUrl "https://api.sunchaser.app" -TelemetryUrl "https://api.sunchaser.app"
param(
  [string]$ApiBaseUrl = "https://api.sunchaser.app",
  [string]$TelemetryUrl = "https://api.sunchaser.app"
)

Push-Location $PSScriptRoot\..
try {
  Write-Host "flutter pub get"
  flutter pub get
  Write-Host "Building Flutter web (release) with API_BASE_URL=$ApiBaseUrl"
  flutter build web --release --dart-define=API_BASE_URL=$ApiBaseUrl --dart-define=TELEMETRY_URL=$TelemetryUrl
} finally {
  Pop-Location
}
