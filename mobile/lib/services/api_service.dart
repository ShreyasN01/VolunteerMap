import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import '../config/api_config.dart';
import '../models/survey.dart';
import '../models/volunteer.dart';
import '../models/match_result.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final Dio _dio = Dio(BaseOptions(
    baseUrl: ApiConfig.baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 30),
  ));

  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get(ApiConfig.health);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<List<Survey>> getAllSurveys() async {
    try {
      final response = await _dio.get(ApiConfig.surveysAll);
      final List data = response.data is Map ? response.data['surveys'] : response.data;
      return data.map((e) => Survey.fromJson(e)).toList();
    } catch (e) {
      return _loadLocalSurveys();
    }
  }

  Future<List<Survey>> getUrgentNeeds() async {
    try {
      final response = await _dio.get(ApiConfig.urgentNeeds);
      final List data = response.data is Map ? response.data['surveys'] : response.data;
      return data.map((e) => Survey.fromJson(e)).toList();
    } catch (e) {
      final local = await _loadLocalSurveys();
      local.sort((a, b) => b.urgencyScore.compareTo(a.urgencyScore));
      return local.take(5).toList();
    }
  }

  Future<Map<String, dynamic>> getClusters() async {
    try {
      final response = await _dio.get(ApiConfig.clusters);
      return response.data as Map<String, dynamic>;
    } catch (e) {
      return {'clusters': []};
    }
  }

  Future<Survey?> submitSurvey(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post(ApiConfig.submitSurvey, data: data);
      return Survey.fromJson(response.data);
    } catch (e) {
      return null;
    }
  }

  Future<Map<String, dynamic>?> uploadOcrImage(File imageFile) async {
    try {
      String fileName = imageFile.path.split('/').last;
      FormData formData = FormData.fromMap({
        "file": await MultipartFile.fromFile(imageFile.path, filename: fileName),
      });
      final response = await _dio.post(ApiConfig.ocrUpload, data: formData);
      return response.data as Map<String, dynamic>;
    } catch (e) {
      return null;
    }
  }

  Future<List<Volunteer>> getAvailableVolunteers() async {
    try {
      final response = await _dio.get(ApiConfig.volunteers);
      final List data = response.data is Map ? response.data['volunteers'] : response.data;
      return data.map((e) => Volunteer.fromJson(e)).toList();
    } catch (e) {
      return _loadLocalVolunteers();
    }
  }

  Future<bool> registerVolunteer(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post(ApiConfig.registerVolunteer, data: data);
      return response.statusCode == 201 || response.statusCode == 200;
    } catch (e) {
      if (e is DioException) {
        debugPrint('Registration failed: ${e.response?.data}');
      } else {
        debugPrint('Registration error: $e');
      }
      return false;
    }
  }

  Future<List<MatchResult>> matchVolunteers() async {
    try {
      final response = await _dio.post(ApiConfig.matchVolunteers);
      final List data = response.data is Map ? response.data['matches'] : response.data;
      return data.map((e) => MatchResult.fromJson(e)).toList();
    } catch (e) {
      return _loadLocalMatches();
    }
  }

  Future<Map<String, dynamic>> getDashboardStats() async {
    try {
      final response = await _dio.get(ApiConfig.stats);
      return response.data as Map<String, dynamic>;
    } catch (e) {
      final surveys = await _loadLocalSurveys();
      return {
        'total_surveys': surveys.length,
        'active_volunteers': 8,
        'urgent_count': surveys.where((s) => s.urgencyScore > 70).length,
        'category_breakdown': {
          'healthcare': surveys.where((s) => s.category == 'healthcare').length,
          'food': surveys.where((s) => s.category == 'food').length,
          'education': surveys.where((s) => s.category == 'education').length,
          'sanitation': surveys.where((s) => s.category == 'sanitation').length,
          'employment': surveys.where((s) => s.category == 'employment').length,
        }
      };
    }
  }

  Future<List<Survey>> _loadLocalSurveys() async {
    try {
      final String data = await rootBundle.loadString('assets/sample_data/surveys.json');
      final List parsed = json.decode(data);
      return parsed.map((e) => Survey.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<Volunteer>> _loadLocalVolunteers() async {
    try {
      final String data = await rootBundle.loadString('assets/sample_data/volunteers.json');
      final List parsed = json.decode(data);
      return parsed.map((e) => Volunteer.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<MatchResult>> _loadLocalMatches() async {
    try {
      final String data = await rootBundle.loadString('assets/sample_data/matches.json');
      final List parsed = json.decode(data);
      return parsed.map((e) => MatchResult.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }
}
