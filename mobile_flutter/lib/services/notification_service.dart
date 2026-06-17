/// Local Notification Service — Shows threat alerts as push-style notifications
/// Works entirely locally — no Firebase needed for local alerts
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _initialized = false;

  /// Initialize the notification plugin
  static Future<void> initialize() async {
    if (_initialized) return;

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidSettings);

    await _plugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (response) {
        debugPrint('[SentinelX] Notification tapped: ${response.payload}');
      },
    );

    // Create notification channel for threat alerts
    const channel = AndroidNotificationChannel(
      'sentinelx_threats',
      'Threat Alerts',
      description: 'Real-time phishing and scam threat alerts',
      importance: Importance.high,
      playSound: true,
      enableVibration: true,
    );

    await _plugin
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);

    _initialized = true;
  }

  /// Show a threat alert notification
  static Future<void> showThreatAlert({
    required String title,
    required String body,
    required double riskScore,
    String? payload,
  }) async {
    await initialize();

    String channelId = 'sentinelx_threats';
    Importance importance = Importance.high;
    Priority priority = Priority.high;

    if (riskScore >= 8.5) {
      importance = Importance.max;
      priority = Priority.max;
    }

    final androidDetails = AndroidNotificationDetails(
      channelId,
      'Threat Alerts',
      channelDescription: 'Real-time phishing and scam alerts',
      importance: importance,
      priority: priority,
      icon: '@mipmap/ic_launcher',
      color: riskScore >= 6.1
          ? const Color(0xFFEF4444)
          : riskScore >= 3.1
              ? const Color(0xFFF59E0B)
              : const Color(0xFF22C55E),
      styleInformation: BigTextStyleInformation(body),
      ticker: 'SentinelX Threat Alert',
    );

    await _plugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      NotificationDetails(android: androidDetails),
      payload: payload,
    );
  }

  /// Show SMS threat notification
  static Future<void> showSmsThreatAlert(
      String sender, double riskScore, String threatLevel) async {
    final emoji = riskScore >= 8.5
        ? '🚨'
        : riskScore >= 6.1
            ? '⚠️'
            : 'ℹ️';

    await showThreatAlert(
      title: '$emoji $threatLevel Risk SMS Detected',
      body: 'Suspicious SMS from $sender detected with risk score ${riskScore.toStringAsFixed(1)}/10',
      riskScore: riskScore,
      payload: 'sms:$sender',
    );
  }
}

