/// Notification Monitor Service — Captures WhatsApp/Telegram/Banking notifications
/// Auto-analyzes and shows alert notifications even in background
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'api_service.dart';
import 'notification_service.dart';

class NotificationMonitorService extends ChangeNotifier {
  static const _channel = MethodChannel('com.sentinelx/notifications');
  bool _isMonitoring = false;
  bool _hasAccess = false;
  List<Map<String, dynamic>> _interceptedNotifications = [];
  List<Map<String, dynamic>> _analysisResults = [];
  ApiService? _apiService;

  bool get isMonitoring => _isMonitoring;
  bool get hasAccess => _hasAccess;
  List<Map<String, dynamic>> get interceptedNotifications => _interceptedNotifications;
  List<Map<String, dynamic>> get analysisResults => _analysisResults;
  int get threatCount => _analysisResults.where((r) => r['threat_detected'] == true).length;

  void setApiService(ApiService service) {
    _apiService = service;
  }

  Future<bool> checkAccess() async {
    try {
      _hasAccess = await _channel.invokeMethod('isNotificationAccessGranted') ?? false;
      notifyListeners();
      return _hasAccess;
    } catch (e) {
      debugPrint('[SentinelX] Notification access check error: $e');
      return false;
    }
  }

  Future<void> requestAccess() async {
    try {
      await _channel.invokeMethod('openNotificationSettings');
    } catch (e) {
      debugPrint('[SentinelX] Could not open notification settings: $e');
    }
  }

  Future<bool> startMonitoring() async {
    try {
      _hasAccess = await checkAccess();
      if (!_hasAccess) {
        await requestAccess();
        return false;
      }

      _channel.setMethodCallHandler(_handleNotification);
      _isMonitoring = true;
      notifyListeners();
      debugPrint('[SentinelX] Notification monitoring started');
      return true;
    } catch (e) {
      debugPrint('[SentinelX] Notification monitoring error: $e');
      return false;
    }
  }

  void stopMonitoring() {
    _isMonitoring = false;
    _channel.setMethodCallHandler(null);
    notifyListeners();
  }

  Future<dynamic> _handleNotification(MethodCall call) async {
    if (call.method == 'onNotificationReceived') {
      final data = Map<String, dynamic>.from(call.arguments);
      await _processNotification(data);
    }
    return null;
  }

  Future<void> _processNotification(Map<String, dynamic> data) async {
    final appName = data['app_name'] ?? 'Unknown';
    final sender = data['sender'] ?? 'Unknown';
    final message = data['message'] ?? '';

    final notifData = {
      'app_name': appName,
      'sender': sender,
      'message': message,
      'timestamp': data['timestamp'] ?? DateTime.now().toIso8601String(),
      'source': 'notification',
      'package': data['package_name'] ?? '',
      'analyzed': false,
      'risk_score': 0.0,
      'threat_detected': false,
      'threat_level': 'SCANNING...',
    };

    _interceptedNotifications.insert(0, notifData);
    if (_interceptedNotifications.length > 200) {
      _interceptedNotifications = _interceptedNotifications.sublist(0, 200);
    }
    notifyListeners();

    // Analyze via backend (no notification until result is ready)
    if (_apiService != null && message.isNotEmpty) {
      try {
        final senderInfo = '$appName — $sender';
        final result = await _apiService!.analyzeSms(senderInfo, message);
        result['source_notification'] = notifData;

        final risk = (result['risk_score'] ?? 0.0).toDouble();
        final detected = result['threat_detected'] == true;
        final reasons = (result['reasons'] as List?)?.cast<String>() ?? [];

        // Determine proper threat label
        String threatLevel;
        if (risk >= 8.5) {
          threatLevel = 'CRITICAL';
        } else if (risk >= 6.1) {
          threatLevel = 'HIGH';
        } else if (risk >= 3.1) {
          threatLevel = 'MEDIUM';
        } else {
          threatLevel = 'LOW';
        }

        result['computed_threat_level'] = threatLevel;
        _analysisResults.insert(0, result);
        if (_analysisResults.length > 100) {
          _analysisResults = _analysisResults.sublist(0, 100);
        }

        // Update the intercepted notification with results
        notifData['analyzed'] = true;
        notifData['risk_score'] = risk;
        notifData['threat_detected'] = detected;
        notifData['threat_level'] = threatLevel;
        notifyListeners();

        // Only show notification if threat is MEDIUM or higher
        if (risk >= 6.1) {
          // HIGH/CRITICAL — urgent alert
          await NotificationService.showThreatAlert(
            title: '🚨 $threatLevel THREAT — $appName',
            body: '⚠️ SCAM ALERT from $sender!\nRisk: ${risk.toStringAsFixed(1)}/10\n${reasons.isNotEmpty ? reasons.first : "Suspicious content detected"}',
            riskScore: risk,
            payload: 'threat:$appName:$sender',
          );
        } else if (risk >= 5.0) {
          // MEDIUM — warning (only score 5.0+)
          await NotificationService.showThreatAlert(
            title: '⚠️ Suspicious $appName Message',
            body: 'From $sender — Risk: ${risk.toStringAsFixed(1)}/10\n${reasons.isNotEmpty ? reasons.first : "Some suspicious patterns found"}',
            riskScore: risk,
            payload: 'warning:$appName:$sender',
          );
        }
        // LOW risk — no notification, just log silently
      } catch (e) {
        debugPrint('[SentinelX] Notification analysis error: $e');
        notifData['analyzed'] = true;
        notifData['threat_level'] = 'ERROR';
        notifyListeners();
      }
    }
  }
}
