class LocationData {
  final String name;
  final double latitude;
  final double longitude;

  LocationData({
    required this.name,
    required this.latitude,
    required this.longitude,
  });

  Map<String, dynamic> toJson() => {
    'name': name,
    'latitude': latitude,
    'longitude': longitude,
  };

  factory LocationData.fromJson(Map<String, dynamic> json) => LocationData(
    name: json['name'],
    latitude: json['latitude'],
    longitude: json['longitude'],
  );
}