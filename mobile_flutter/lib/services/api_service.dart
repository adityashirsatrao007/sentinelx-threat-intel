/// API Service — handles all backend API calls
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

class ApiService {
  final String token;
  ApiService(this.token);

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      };

  // ─── Dashboard ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getStats() async {
    final resp = await http.get(Uri.parse(ApiConfig.dashboardStats), headers: _headers);
    if (resp.statusCode == 200) return jsonDecode(resp.body);
    throw Exception('Failed to load stats: ${resp.statusCode}');
  }

  Future<List<dynamic>> getThreats({int limit = 20}) async {
    final resp = await http.get(
      Uri.parse('${ApiConfig.dashboardThreats}?limit=$limit'),
      headers: _headers,
    );
    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);
      return data['threats'] ?? [];
    }
    throw Exception('Failed to load threats');
  }

  Future<List<dynamic>> getTrends({int days = 7}) async {
    final resp = await http.get(
      Uri.parse('${ApiConfig.dashboardTrends}?days=$days'),
      headers: _headers,
    );
    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);
      return data['trends'] ?? [];
    }
    throw Exception('Failed to load trends');
  }

  // ─── Alerts ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getAlerts({int limit = 50, bool unacknowledgedOnly = false}) async {
    final resp = await http.get(
      Uri.parse('${ApiConfig.alerts}?limit=$limit&unacknowledged_only=$unacknowledgedOnly'),
      headers: _headers,
    );
    if (resp.statusCode == 200) return jsonDecode(resp.body);
    throw Exception('Failed to load alerts');
  }

  Future<void> acknowledgeAlert(String alertId) async {
    await http.post(
      Uri.parse('${ApiConfig.alerts}/$alertId/acknowledge'),
      headers: _headers,
    );
  }

  // ─── Analysis ──────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> analyzeSms(String sender, String message) async {
    final resp = await http.post(
      Uri.parse(ApiConfig.analyzeSms),
      headers: _headers,
      body: jsonEncode({'sender': sender, 'message': message}),
    );
    if (resp.statusCode == 200) return jsonDecode(resp.body);
    throw Exception('SMS analysis failed: ${resp.statusCode}');
  }

  Future<Map<String, dynamic>> analyzeEmail(String sender, String subject, String body) async {
    final resp = await http.post(
      Uri.parse(ApiConfig.analyzeEmail),
      headers: _headers,
      body: jsonEncode({'sender': sender, 'subject': subject, 'body': body}),
    );
    if (resp.statusCode == 200) return jsonDecode(resp.body);
    throw Exception('Email analysis failed: ${resp.statusCode}');
  }

  // ─── Health ────────────────────────────────────────────────────────────────

  Future<bool> checkHealth() async {
    try {
      final resp = await http.get(Uri.parse(ApiConfig.health)).timeout(
        const Duration(seconds: 5),
      );
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
