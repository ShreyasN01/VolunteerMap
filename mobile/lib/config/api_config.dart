class ApiConfig {
  // Use 127.0.0.1 for iOS/macOS simulators.
  // Use 10.0.2.2 for Android emulators.
  // Use your computer's local IP (e.g., 10.42.144.67) for physical phones.
  static const String baseUrl = 'http://127.0.0.1:8000';
  static const String surveysAll = '/surveys/all';
  static const String submitSurvey = '/surveys/submit';
  static const String clusters = '/surveys/clusters';
  static const String urgentNeeds = '/surveys/urgent';
  static const String ocrUpload = '/surveys/ocr';
  static const String volunteers = '/volunteers/available';
  static const String registerVolunteer = '/volunteers/register';
  static const String matchVolunteers = '/volunteers/match';
  static const String stats = '/dashboard/stats';
  static const String health = '/health';
}
