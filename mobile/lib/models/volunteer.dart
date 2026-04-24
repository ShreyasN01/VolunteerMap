class Volunteer {
  final String id;
  final String name;
  final String phone;
  final List<String> skills;
  final bool available;
  final double latitude;
  final double longitude;
  final String district;
  final List<String> languages;

  Volunteer({
    required this.id,
    required this.name,
    required this.phone,
    required this.skills,
    required this.available,
    required this.latitude,
    required this.longitude,
    required this.district,
    required this.languages,
  });

  factory Volunteer.fromJson(Map<String, dynamic> json) {
    return Volunteer(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      phone: json['phone'] ?? '',
      skills: List<String>.from(json['skills'] ?? []),
      available: json['available'] ?? false,
      latitude: (json['location']?['latitude'] ?? json['latitude'] ?? 0.0).toDouble(),
      longitude: (json['location']?['longitude'] ?? json['longitude'] ?? 0.0).toDouble(),
      district: json['district'] ?? '',
      languages: List<String>.from(json['languages'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'phone': phone,
      'skills': skills,
      'available': available,
      'location': {'latitude': latitude, 'longitude': longitude},
      'district': district,
      'languages': languages,
    };
  }

  String get initials {
    if (name.isEmpty) return 'V';
    List<String> names = name.trim().split(' ');
    if (names.length > 1) {
      return (names[0][0] + names[names.length - 1][0]).toUpperCase();
    }
    return names[0][0].toUpperCase();
  }
}
