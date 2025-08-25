import 'package:flutter/material.dart';
import 'package:sunshine_spotter/models/location.dart';
import 'package:sunshine_spotter/screens/results_screen.dart';
import 'package:sunshine_spotter/screens/favorites_screen.dart';
import 'package:sunshine_spotter/screens/settings_screen.dart';
import 'package:sunshine_spotter/services/location_service.dart';
import 'package:sunshine_spotter/services/telemetry_service.dart';
import 'package:sunshine_spotter/widgets/area_selection_card.dart';
import 'package:sunshine_spotter/widgets/location_selection_card.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> with TickerProviderStateMixin {
  LocationData? selectedLocation;
  LocationData? lastUsedLocation;
  double selectedRadius = 25.0; // Default to nearby
  bool isLoading = false;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;
  final TextEditingController _typedLocationController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.forward();
    _loadLastUsedLocation();
  }

  void _loadLastUsedLocation() async {
    final lastLocation = await LocationService.getLastUsedLocation();
    if (lastLocation != null) {
      setState(() {
        lastUsedLocation = lastLocation;
        selectedLocation = lastLocation; // Auto-select the last used location
      });
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _onAreaSelected(double radius) {
    setState(() {
      selectedRadius = radius;
    });
  }

  void _onUseCurrentLocation() async {
    setState(() {
      isLoading = true;
    });
    
    final location = await LocationService.getCurrentLocation();
    if (location != null) {
      setState(() {
        selectedLocation = location;
        isLoading = false;
      });
      _searchSunshine();
    } else {
      setState(() {
        isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Unable to access location. Please enable location services.')),
        );
      }
    }
  }

  void _onUseLastLocation() {
    if (lastUsedLocation != null) {
      setState(() {
        selectedLocation = lastUsedLocation;
      });
    }
  }

  void _searchSunshine() async {
    final q = _typedLocationController.text.trim();
    if (q.isNotEmpty) {
      // Text-based search path
      if (mounted) {
        TelemetryService.logEvent('navigation', properties: {
          'from_screen': 'home',
          'to_screen': 'results',
          'q': q,
          'search_radius': selectedRadius,
        });

        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => ResultsScreen(
              location: null,
              radius: selectedRadius,
              q: q,
            ),
          ),
        );
      }
      return;
    }

    if (selectedLocation != null) {
      // Save the location as last used
      await LocationService.saveLastUsedLocation(selectedLocation!);
      
      // Update lastUsedLocation in state
      setState(() {
        lastUsedLocation = selectedLocation;
      });
      
      if (mounted) {
        TelemetryService.logEvent('navigation', properties: {
          'from_screen': 'home',
          'to_screen': 'results',
          'location_lat': selectedLocation!.latitude.toStringAsFixed(4),
          'location_lon': selectedLocation!.longitude.toStringAsFixed(4),
          'search_radius': selectedRadius,
        });

        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => ResultsScreen(
              location: selectedLocation!,
              radius: selectedRadius,
            ),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeAnimation,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 20),
                
                // Header
                Text(
                  '☀️ Sunshine Spotter',
                  style: theme.textTheme.displaySmall?.copyWith(
                    color: theme.colorScheme.primary,
                    fontWeight: FontWeight.bold,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  'Find sunny spots near you',
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                  textAlign: TextAlign.center,
                ),
                
                const SizedBox(height: 40),

                // Typed location input
                TextField(
                  controller: _typedLocationController,
                  decoration: InputDecoration(
                    labelText: 'Type a city or place (optional)',
                    hintText: 'e.g. "Seattle, WA"',
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.search),
                      onPressed: _searchSunshine,
                    ),
                  ),
                  onSubmitted: (_) => _searchSunshine(),
                ),
                const SizedBox(height: 20),
                
                // Location Selection
                LocationSelectionCard(
                  selectedLocation: selectedLocation,
                  lastUsedLocation: lastUsedLocation,
                  onUseCurrentLocation: _onUseCurrentLocation,
                  onUseLastLocation: _onUseLastLocation,
                  isLoading: isLoading,
                ),
                
                const SizedBox(height: 24),
                
                // Area Selection
                AreaSelectionCard(
                  selectedRadius: selectedRadius,
                  onAreaSelected: _onAreaSelected,
                ),
                
                const SizedBox(height: 32),
                
                // Find Sunshine Button
                Container(
                  height: 56,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [theme.colorScheme.primary, theme.colorScheme.secondary],
                    ),
                    borderRadius: BorderRadius.circular(28),
                  ),
                  child: ElevatedButton(
                    onPressed: selectedLocation != null ? _searchSunshine : _onUseCurrentLocation,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      shadowColor: Colors.transparent,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
                    ),
                    child: Text(
                      selectedLocation != null ? 'Find Sunshine ☀️' : 'Find Sunshine Near Me ☀️',
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: theme.colorScheme.onPrimary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
                
                const SizedBox(height: 32),
                
                // Quick Actions
                Row(
                  children: [
                    Expanded(
                      child: _QuickActionCard(
                        icon: Icons.favorite,
                        title: 'Favorites',
                        subtitle: 'Saved spots',
                        onTap: () {
                          TelemetryService.logEvent('navigation', properties: {
                            'from_screen': 'home',
                            'to_screen': 'favorites',
                          });
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const FavoritesScreen()),
                          );
                        },
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _QuickActionCard(
                        icon: Icons.settings,
                        title: 'Settings',
                        subtitle: 'Preferences',
                        onTap: () {
                          TelemetryService.logEvent('navigation', properties: {
                            'from_screen': 'home',
                            'to_screen': 'settings',
                          });
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const SettingsScreen()),
                          );
                        },
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _QuickActionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _QuickActionCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            children: [
              Icon(
                icon,
                size: 32,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(height: 8),
              Text(
                title,
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}