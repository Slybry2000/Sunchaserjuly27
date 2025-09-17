class SunshineSpot {
  final String id;
  final String name;
  final String description;
  final double latitude;
  final double longitude;
  final String imageUrl;
  final String? apiPhotoId; // Unsplash API photo id for meta/track
  final int sunshineHours;
  final double temperature;
  final String weather;
  final double rating;
  final String category;
  final double distance;
  final bool isFavorite;

  SunshineSpot({
    required this.id,
    required this.name,
    required this.description,
    required this.latitude,
    required this.longitude,
    required this.imageUrl,
  this.apiPhotoId,
    required this.sunshineHours,
    required this.temperature,
    required this.weather,
    required this.rating,
    required this.category,
    required this.distance,
    this.isFavorite = false,
  });

  SunshineSpot copyWith({
    String? id,
    String? name,
    String? description,
    double? latitude,
    double? longitude,
    String? imageUrl,
  String? apiPhotoId,
    int? sunshineHours,
    double? temperature,
    String? weather,
    double? rating,
    String? category,
    double? distance,
    bool? isFavorite,
  }) => SunshineSpot(
    id: id ?? this.id,
    name: name ?? this.name,
    description: description ?? this.description,
    latitude: latitude ?? this.latitude,
    longitude: longitude ?? this.longitude,
    imageUrl: imageUrl ?? this.imageUrl,
  apiPhotoId: apiPhotoId ?? this.apiPhotoId,
    sunshineHours: sunshineHours ?? this.sunshineHours,
    temperature: temperature ?? this.temperature,
    weather: weather ?? this.weather,
    rating: rating ?? this.rating,
    category: category ?? this.category,
    distance: distance ?? this.distance,
    isFavorite: isFavorite ?? this.isFavorite,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'description': description,
    'latitude': latitude,
    'longitude': longitude,
    'imageUrl': imageUrl,
  'apiPhotoId': apiPhotoId,
    'sunshineHours': sunshineHours,
    'temperature': temperature,
    'weather': weather,
    'rating': rating,
    'category': category,
    'distance': distance,
    'isFavorite': isFavorite,
  };

  factory SunshineSpot.fromJson(Map<String, dynamic> json) => SunshineSpot(
    id: json['id'],
    name: json['name'],
    description: json['description'],
    latitude: json['latitude'],
    longitude: json['longitude'],
    imageUrl: json['imageUrl'],
  apiPhotoId: json['apiPhotoId'],
    sunshineHours: json['sunshineHours'],
    temperature: json['temperature'],
    weather: json['weather'],
    rating: json['rating'],
    category: json['category'],
    distance: json['distance'],
    isFavorite: json['isFavorite'] ?? false,
  );
}