import 'package:flutter/material.dart';
import '../models/volunteer.dart';
import '../models/match_result.dart';
import '../services/api_service.dart';

class VolunteerProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  List<Volunteer> _volunteers = [];
  List<MatchResult> _matchResults = [];
  bool _isLoading = false;
  bool _isMatchingInProgress = false;

  List<Volunteer> get volunteers => _volunteers;
  List<MatchResult> get matchResults => _matchResults;
  bool get isLoading => _isLoading;
  bool get isMatchingInProgress => _isMatchingInProgress;

  Future<void> fetchVolunteers() async {
    _isLoading = true;
    notifyListeners();
    try {
      _volunteers = await _apiService.getAvailableVolunteers();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> registerVolunteer(Map<String, dynamic> data) async {
    _isLoading = true;
    notifyListeners();
    try {
      final success = await _apiService.registerVolunteer(data);
      if (success) await fetchVolunteers();
      return success;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> runMatching() async {
    _isMatchingInProgress = true;
    notifyListeners();
    try {
      // Artificial delay for "Gemini is analysing..." effect
      await Future.delayed(const Duration(seconds: 2));
      _matchResults = await _apiService.matchVolunteers();
    } finally {
      _isMatchingInProgress = false;
      notifyListeners();
    }
  }
}
