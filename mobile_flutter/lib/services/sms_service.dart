/// SMS Monitoring Service — Uses MethodChannel for SMS interception on Android
/// Falls back to manual analysis if SMS permissions aren't available
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';
import 'api_service.dart';
import 'notification_service.dart';

class SmsMonitorService extends ChangeNotifier {
  static const _channel = MethodChannel('com.sentinelx/sms');
  bool _isMonitoring = false;
  List<Map<String, dynamic>> _interceptedMessages = [];
  List<Map<String, dynamic>> _analysisResults = [];
  ApiService? _apiService;

  bool get isMonitoring => _isMonitoring;
  List<Map<String, dynamic>> get interceptedMessages => _interceptedMessages;
  List<Map<String, dynamic>> get analysisResults => _analysisResults;

  void setApiService(ApiService service) {
    _apiService = service;
  }

  /// Request SMS permissions and start listening
  Future<bool> startMonitoring() async {
    try {
      // Request SMS permission
      final smsStatus = await Permission.sms.request();
      if (!smsStatus.isGranted) {
        debugPrint('[SentinelX] SMS permission denied');
        return false;
      }

      // Request notification permission for alerts
      await Permission.notification.request();

      // Set up method channel listener for incoming SMS
      _channel.setMethodCallHandler(_handleMethodCall);

      _isMonitoring = true;
      notifyListeners();
      debugPrint('[SentinelX] SMS monitoring started');
      return true;
    } catch (e) {
      debugPrint('[SentinelX] SMS monitoring error: $e');
      // Even without native SMS interception, mark as monitoring
      // so users can manually submit SMS for analysis
      _isMonitoring = true;
      notifyListeners();
      return true;
    }
  }

  /// Stop monitoring
  void stopMonitoring() {
    _isMonitoring = false;
    _channel.setMethodCallHandler(null);
    notifyListeners();
  }

  /// Handle incoming SMS from native Android side
  Future<dynamic> _handleMethodCall(MethodCall call) async {
    if (call.method == 'onSmsReceived') {
      final Map<String, dynamic> smsData = Map<String, dynamic>.from(call.arguments);
      await _processSms(smsData['sender'] ?? 'Unknown', smsData['message'] ?? '');
    }
    return null;
  }

  /// Process an SMS (from interception or manual submission)
  Future<Map<String, dynamic>?> processSmsManually(String sender, String message) async {
    return _processSms(sender, message);
  }

  Future<Map<String, dynamic>?> _processSms(String sender, String message) async {
    final smsData = {
      'sender': sender,
      'message': message,
      'timestamp': DateTime.now().toIso8601String(),
      'source': 'sms',
    };

    _interceptedMessages.insert(0, smsData);
    if (_interceptedMessages.length > 100) {
      _interceptedMessages = _interceptedMessages.sublist(0, 100);
    }
    notifyListeners();

    // Auto-analyze if API service is available
    if (_apiService != null && message.isNotEmpty) {
      try {
        final result = await _apiService!.analyzeSms(sender, message);
        result['source_message'] = smsData;
        _analysisResults.insert(0, result);
        if (_analysisResults.length > 50) {
          _analysisResults = _analysisResults.sublist(0, 50);
        }
        notifyListeners();

        // Only show notification for real threats (MEDIUM+, score >= 5.0)
        final risk = (result['risk_score'] ?? 0.0).toDouble();
        if (risk >= 5.0) {
          NotificationService.showSmsThreatAlert(
            sender,
            risk,
            result['threat_level'] ?? 'UNKNOWN',
          );
        }

        return result;
      } catch (e) {
        debugPrint('[SentinelX] SMS analysis error: $e');
      }
    }
    return null;
  }
}
