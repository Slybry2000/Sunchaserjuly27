import 'package:flutter/material.dart';
import 'package:sunshine_spotter/screens/home_screen.dart';
import 'package:sunshine_spotter/theme.dart';

void main() {
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
