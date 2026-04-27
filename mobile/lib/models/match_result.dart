import 'package:flutter/material.dart';

class MatchResult {
  final String volunteerId;
  final String volunteerName;
  final String needId;
  final String needCategory;
  final String needDistrict;
  final String matchReason;
  final String taskSummary;
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
    required this.taskSummary,
    required this.matchScore,
    required this.priority,
    required this.distance,
  });

  factory MatchResult.fromJson(Map<String, dynamic> json) {
    return MatchResult(
      volunteerId: json['volunteer_id'] ?? '',
      volunteerName: json['volunteer_name'] ?? '',
      needId: json['need_id'] ?? '',
      needCategory: json['need_category'] ?? json['category'] ?? '',
      needDistrict: json['need_district'] ?? json['district'] ?? '',
      matchReason: json['match_reason'] ?? '',
      taskSummary: json['task_summary'] ?? '',
      matchScore: (json['match_score'] ?? 0.8).toDouble(),
      priority: json['priority'] ?? 'medium',
      distance: (json['distance'] ?? json['estimated_travel_km'] ?? 0.0).toDouble(),
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

  /// Returns a human-readable explanation of how the AI determined this match.
  String get matchBasis {
    final factors = <String>[];
    if (needCategory.isNotEmpty) {
      factors.add('Category: ${needCategory[0].toUpperCase()}${needCategory.substring(1)}');
    }
    if (distance > 0) {
      factors.add('Distance: ${distance.toStringAsFixed(1)} km');
    }
    if (matchScore > 0) {
      factors.add('Match Score: ${(matchScore * 100).toInt()}%');
    }
    if (priority.isNotEmpty) {
      factors.add('Priority: ${priority[0].toUpperCase()}${priority.substring(1)}');
    }
    return factors.join(' • ');
  }
}
