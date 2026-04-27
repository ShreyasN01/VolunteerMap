import 'package:flutter/material.dart';
import '../services/api_service.dart';

class DashboardProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  int _totalSurveys = 0;
  int _activeVolunteers = 0;
  int _urgentCount = 0;
  Map<String, int> _categoryBreakdown = {};
  bool _isLoading = false;

  int get totalSurveys => _totalSurveys;
  int get activeVolunteers => _activeVolunteers;
  int get urgentCount => _urgentCount;
  Map<String, int> get categoryBreakdown => _categoryBreakdown;
  bool get isLoading => _isLoading;

  Future<void> fetchStats() async {
    _isLoading = true;
    notifyListeners();
    try {
      final stats = await _apiService.getDashboardStats();
      _totalSurveys = stats['total_surveys'] ?? 0;
      _activeVolunteers = stats['active_volunteers'] ?? stats['total_volunteers'] ?? 0;
      _urgentCount = stats['urgent_count'] ?? stats['urgent_needs'] ?? 0;
      _categoryBreakdown = Map<String, int>.from(stats['category_breakdown'] ?? {});
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
