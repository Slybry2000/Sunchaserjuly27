import 'package:flutter/material.dart';
import 'package:sunshine_spotter/screens/home_screen.dart';
import 'package:sunshine_spotter/theme.dart';
import 'services/telemetry_service.dart' as telemetry;

// Allow build-time override with --dart-define=TELEMETRY_URL
const _kTelemetryUrl = String.fromEnvironment('TELEMETRY_URL', defaultValue: '');

void main() {
  if (_kTelemetryUrl.isNotEmpty) {
    telemetry.telemetryBaseUrl = _kTelemetryUrl;
  } else {
    // In debug mode, default to local backend
    assert(() {
      telemetry.telemetryBaseUrl = 'http://localhost:8000';
      return true;
    }());
  }

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sunshine Spotter',
      debugShowCheckedModeBanner: false,
      theme: lightTheme,
      darkTheme: darkTheme,
      themeMode: ThemeMode.system,
      home: const HomePage(), // TODO(agent): please implement.
    );
  }
}
