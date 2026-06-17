/// Authentication Service — JWT token management + API calls
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class AuthService extends ChangeNotifier {
  String? _token;
  Map<String, dynamic>? _user;
  bool _loading = false;

  String? get token => _token;
  Map<String, dynamic>? get user => _user;
  bool get isLoggedIn => _token != null;
  bool get loading => _loading;
  String get userName => _user?['name'] ?? 'User';
  String get userEmail => _user?['email'] ?? '';
  String get userRole => _user?['role'] ?? 'user';

  Map<String, String> get authHeaders => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  /// Try to restore saved token on app start
  Future<void> tryAutoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString('auth_token');
    if (saved == null) return;

    _token = saved;
    try {
      await fetchMe();
    } catch (_) {
      _token = null;
      await prefs.remove('auth_token');
    }
    notifyListeners();
  }

  /// Login with email + password
  Future<String?> login(String email, String password) async {
    _loading = true;
    notifyListeners();

    try {
      final resp = await http.post(
        Uri.parse(ApiConfig.login),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        _token = data['access_token'];
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', _token!);
        await fetchMe();
        _loading = false;
        notifyListeners();
        return null; // success
      } else {
        _loading = false;
        notifyListeners();
        final err = jsonDecode(resp.body);
        return err['detail'] ?? 'Login failed';
      }
    } catch (e) {
      _loading = false;
      notifyListeners();
      return 'Connection error: $e';
    }
  }

  /// Register new account
  Future<String?> register(String name, String email, String password) async {
    _loading = true;
    notifyListeners();

    try {
      final resp = await http.post(
        Uri.parse(ApiConfig.register),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'name': name, 'email': email, 'password': password}),
      );

      _loading = false;
      notifyListeners();

      if (resp.statusCode == 201) {
        return null; // success — now login
      } else {
        final err = jsonDecode(resp.body);
        return err['detail'] ?? 'Registration failed';
      }
    } catch (e) {
      _loading = false;
      notifyListeners();
      return 'Connection error: $e';
    }
  }

  /// Fetch current user profile
  Future<void> fetchMe() async {
    final resp = await http.get(
      Uri.parse(ApiConfig.me),
      headers: authHeaders,
    );
    if (resp.statusCode == 200) {
      _user = jsonDecode(resp.body);
    }
  }

  /// Logout
  Future<void> logout() async {
    _token = null;
    _user = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    notifyListeners();
  }
}
