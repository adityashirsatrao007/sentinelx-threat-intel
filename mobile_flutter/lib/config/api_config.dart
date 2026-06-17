/// SentinelX API Configuration
/// Pointing to hosted backend on Render
class ApiConfig {
  // ─── Production Backend ────────────────────────────────────────────────────
  static const String baseUrl = 'https://sentinelx-48vt.onrender.com';
  static const String apiUrl = '$baseUrl/api/v1';

  // ─── Endpoints ─────────────────────────────────────────────────────────────
  static const String login = '$apiUrl/auth/login';
  static const String register = '$apiUrl/auth/register';
  static const String me = '$apiUrl/auth/me';
  static const String analyzeEmail = '$apiUrl/analyze/email';
  static const String analyzeSms = '$apiUrl/analyze/sms';
  static const String analyzeCall = '$apiUrl/analyze/call';
  static const String dashboardStats = '$apiUrl/dashboard/stats';
  static const String dashboardThreats = '$apiUrl/dashboard/threats';
  static const String dashboardTrends = '$apiUrl/dashboard/trends';
  static const String alerts = '$apiUrl/alerts';
  static const String gmailConnect = '$apiUrl/gmail/connect';
  static const String gmailAccounts = '$apiUrl/gmail/accounts';
  static const String emailConnect = '$apiUrl/email/connect';
  static const String emailAccounts = '$apiUrl/email/accounts';
  static const String emailScan = '$apiUrl/email/scan';
  static const String registerDevice = '$apiUrl/users/me/devices';
  static const String health = '$baseUrl/health';
}
