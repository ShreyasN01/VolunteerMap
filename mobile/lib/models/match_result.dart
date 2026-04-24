import 'package:flutter/material.dart';

class MatchResult {
  final String volunteerId;
  final String volunteerName;
  final String needId;
  final String needCategory;
  final String needDistrict;
  final String matchReason;
  final double matchScore;
  final String priority;
  final double distance;

  MatchResult({
    required this.volunteerId,
    required this.volunteerName,
    required this.needId,
    required this.needCategory,
    required this.needDistrict,
    required this.matchReason,
    required this.matchScore,
    required this.priority,
    required this.distance,
  });

  factory MatchResult.fromJson(Map<String, dynamic> json) {
    return MatchResult(
      volunteerId: json['volunteer_id'] ?? '',
      volunteerName: json['volunteer_name'] ?? '',
      needId: json['need_id'] ?? '',
      needCategory: json['need_category'] ?? '',
      needDistrict: json['need_district'] ?? '',
      matchReason: json['match_reason'] ?? '',
      matchScore: (json['match_score'] ?? 0.0).toDouble(),
      priority: json['priority'] ?? 'Medium',
      distance: (json['distance'] ?? 0.0).toDouble(),
    );
  }

  Color get priorityColor {
    switch (priority.toLowerCase()) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.green;
      default:
        return Colors.blue;
    }
  }
}
