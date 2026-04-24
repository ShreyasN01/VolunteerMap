import 'package:flutter/material.dart';
import '../models/survey.dart';
import '../services/api_service.dart';

class SurveyProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  List<Survey> _surveys = [];
  List<Survey> _urgentNeeds = [];
  bool _isLoading = false;
  String? _error;

  List<Survey> get surveys => _surveys;
  List<Survey> get urgentNeeds => _urgentNeeds;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchSurveys() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _surveys = await _apiService.getAllSurveys();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchUrgentNeeds() async {
    _isLoading = true;
    notifyListeners();
    try {
      _urgentNeeds = await _apiService.getUrgentNeeds();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> submitSurvey(Map<String, dynamic> data) async {
    _isLoading = true;
    notifyListeners();
    try {
      final result = await _apiService.submitSurvey(data);
      if (result != null) {
        _surveys.insert(0, result);
        return true;
      }
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  List<Survey> filterByCategory(String category) {
    if (category == 'All') return _surveys;
    return _surveys.where((s) => s.category.toLowerCase() == category.toLowerCase()).toList();
  }
}
