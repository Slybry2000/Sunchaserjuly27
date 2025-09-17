// Central runtime-ish configuration utilities.
// Provides a single place to derive the API base URL. We avoid using a
// const String.fromEnvironment directly in widgets so hot restart / different
// dart-define invocations pick it up without a full rebuild confusion.
//
// Usage: final base = apiBaseUrl();
String apiBaseUrl() {
  // For web local dev we prefer localhost over Android emulator alias.
  const fromEnv = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');
  return fromEnv.trim();
}
