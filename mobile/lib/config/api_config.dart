class ApiConfig {
  // Production: Vercel hosted backend
  // For local dev: use 'http://127.0.0.1:8000'
  static const String baseUrl = 'https://volunteer-map-2hph.vercel.app';
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
