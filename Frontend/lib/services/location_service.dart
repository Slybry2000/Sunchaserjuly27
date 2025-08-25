import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sunshine_spotter/models/location.dart';
import 'package:sunshine_spotter/services/telemetry_service.dart';

class LocationService {
  static Future<LocationData?> getCurrentLocation() async {
    final stopwatch = Stopwatch()..start();
    
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        TelemetryService.logEvent('location_error', properties: {
          'error': 'service_disabled',
        });
        return null;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          TelemetryService.logEvent('location_error', properties: {
            'error': 'permission_denied',
          });
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        TelemetryService.logEvent('location_error', properties: {
          'error': 'permission_denied_forever',
        });
        return null;
      }

      Position position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
      );

      stopwatch.stop();
      TelemetryService.logEvent('location_acquired', properties: {
        'latitude': position.latitude.toStringAsFixed(4),
        'longitude': position.longitude.toStringAsFixed(4),
        'accuracy': position.accuracy,
        'duration_ms': stopwatch.elapsedMilliseconds,
      });

      return LocationData(
        name: 'Current Location',
        latitude: position.latitude,
        longitude: position.longitude,
      );
    } catch (e) {
      stopwatch.stop();
      TelemetryService.logError('Location acquisition failed', context: 'getCurrentLocation', exception: e);
      return null;
    }
  }

  static double calculateDistance(
    double lat1, double lon1, double lat2, double lon2,
  ) {
    return Geolocator.distanceBetween(lat1, lon1, lat2, lon2) / 1609.34; // Convert to miles
  }

  static Future<void> saveLastUsedLocation(LocationData location) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('last_used_location_name', location.name);
    await prefs.setDouble('last_used_location_lat', location.latitude);
    await prefs.setDouble('last_used_location_lng', location.longitude);
  }

  static Future<LocationData?> getLastUsedLocation() async {
    final prefs = await SharedPreferences.getInstance();
    final name = prefs.getString('last_used_location_name');
    final lat = prefs.getDouble('last_used_location_lat');
    final lng = prefs.getDouble('last_used_location_lng');
    
    if (name != null && lat != null && lng != null) {
      return LocationData(name: name, latitude: lat, longitude: lng);
    }
    
    // Return Renton as default if no last used location
    return LocationData(
      name: 'Renton, WA',
      latitude: 47.4829,
      longitude: -122.2171,
    );
  }
}