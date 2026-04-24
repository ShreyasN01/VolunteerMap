import 'package:flutter/material.dart';

class Survey {
  final String id;
  final DateTime submittedAt;
  final double latitude;
  final double longitude;
  final String district;
  final String state;
  final String category;
  final String description;
  final int severity;
  final int affectedCount;
  final String source;
  final double urgencyScore;

  Survey({
    required this.id,
    required this.submittedAt,
    required this.latitude,
    required this.longitude,
    required this.district,
    required this.state,
    required this.category,
    required this.description,
    required this.severity,
    required this.affectedCount,
    required this.source,
    required this.urgencyScore,
  });

  factory Survey.fromJson(Map<String, dynamic> json) {
    return Survey(
      id: json['id'] ?? '',
      submittedAt: DateTime.parse(json['submitted_at'] ?? DateTime.now().toIso8601String()),
      latitude: (json['location']?['latitude'] ?? json['latitude'] ?? 0.0).toDouble(),
      longitude: (json['location']?['longitude'] ?? json['longitude'] ?? 0.0).toDouble(),
      district: json['district'] ?? '',
      state: json['state'] ?? '',
      category: json['category'] ?? '',
      description: json['description'] ?? '',
      severity: json['severity'] ?? 0,
      affectedCount: json['affected_count'] ?? 0,
      source: json['source'] ?? '',
      urgencyScore: (json['urgency_score'] ?? 0.0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'submitted_at': submittedAt.toIso8601String(),
      'location': {'latitude': latitude, 'longitude': longitude},
      'district': district,
      'state': state,
      'category': category,
      'description': description,
      'severity': severity,
      'affected_count': affectedCount,
      'source': source,
      'urgency_score': urgencyScore,
    };
  }

  Color get categoryColor {
    switch (category.toLowerCase()) {
      case 'healthcare':
        return Colors.red;
      case 'food':
        return Colors.orange;
      case 'education':
        return Colors.blue;
      case 'sanitation':
        return Colors.green;
      case 'employment':
        return Colors.purple;
      default:
        return Colors.teal;
    }
  }

  String get categoryEmoji {
    switch (category.toLowerCase()) {
      case 'healthcare':
        return '🏥';
      case 'food':
        return '🌾';
      case 'education':
        return '📚';
      case 'sanitation':
        return '💧';
      case 'employment':
        return '💼';
      default:
        return '📋';
    }
  }
}
