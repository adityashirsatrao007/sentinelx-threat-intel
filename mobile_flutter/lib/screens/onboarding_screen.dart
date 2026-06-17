/// Onboarding Screen — Guides user through permissions on first launch
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/services.dart';
import '../config/theme.dart';

class OnboardingScreen extends StatefulWidget {
  final VoidCallback onComplete;
  const OnboardingScreen({super.key, required this.onComplete});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _controller = PageController();
  int _currentPage = 0;

  // Permission states
  bool _smsGranted = false;
  bool _notifGranted = false;
  bool _notifListenerGranted = false;

  final _pages = const [
    _PageData(
      icon: Icons.shield,
      gradient: [Color(0xFF3B82F6), Color(0xFF8B5CF6)],
      title: 'Welcome to SentinelX',
      subtitle: 'AI-Powered Threat Detection',
      description: 'Protect yourself from phishing, scams, and social engineering attacks across SMS, WhatsApp, Telegram, and email.',
    ),
    _PageData(
      icon: Icons.sms,
      gradient: [Color(0xFF22C55E), Color(0xFF16A34A)],
      title: 'SMS Protection',
      subtitle: 'Automatic SMS Scanning',
      description: 'SentinelX monitors incoming SMS messages in real-time and alerts you when suspicious content is detected.\n\nWe need SMS permission to read incoming messages.',
    ),
    _PageData(
      icon: Icons.notifications_active,
      gradient: [Color(0xFFF59E0B), Color(0xFFEA580C)],
      title: 'App Monitoring',
      subtitle: 'WhatsApp, Telegram & Banking',
      description: 'Monitor notifications from WhatsApp, Telegram, and banking apps for phishing links and scam messages.\n\nThis requires Notification Access permission.',
    ),
    _PageData(
      icon: Icons.verified_user,
      gradient: [Color(0xFF3B82F6), Color(0xFF06B6D4)],
      title: 'You\'re All Set!',
      subtitle: 'Protection Activated',
      description: 'SentinelX will now monitor your communications in the background and alert you to threats in real-time.\n\nStay safe!',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _checkPermissions();
  }

  Future<void> _checkPermissions() async {
    final sms = await Permission.sms.status;
    setState(() => _smsGranted = sms.isGranted);

    try {
      const channel = MethodChannel('com.sentinelx/notifications');
      final result = await channel.invokeMethod('isNotificationAccessGranted');
      setState(() => _notifListenerGranted = result == true);
    } catch (_) {}
  }

  Future<void> _requestSmsPermission() async {
    final status = await Permission.sms.request();
    setState(() => _smsGranted = status.isGranted);
  }

  Future<void> _requestNotificationPermission() async {
    // Request POST_NOTIFICATIONS permission
    final status = await Permission.notification.request();
    setState(() => _notifGranted = status.isGranted);
  }

  Future<void> _openNotificationListenerSettings() async {
    try {
      const channel = MethodChannel('com.sentinelx/notifications');
      await channel.invokeMethod('openNotificationSettings');
    } catch (_) {}
  }

  Future<void> _completeOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('onboarding_complete', true);
    widget.onComplete();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Page indicator
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(_pages.length, (i) => AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: _currentPage == i ? 32 : 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: _currentPage == i ? AppTheme.accent : AppTheme.surfaceLight,
                    borderRadius: BorderRadius.circular(4),
                  ),
                )),
              ),
            ),

            // Pages
            Expanded(
              child: PageView.builder(
                controller: _controller,
                onPageChanged: (i) => setState(() => _currentPage = i),
                itemCount: _pages.length,
                itemBuilder: (context, i) => _buildPage(i),
              ),
            ),

            // Bottom buttons
            Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                children: [
                  if (_currentPage > 0)
                    TextButton(
                      onPressed: () => _controller.previousPage(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeInOut,
                      ),
                      child: const Text('Back'),
                    ),
                  const Spacer(),
                  if (_currentPage < _pages.length - 1)
                    ElevatedButton(
                      onPressed: () => _controller.nextPage(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeInOut,
                      ),
                      child: const Text('Next'),
                    )
                  else
                    ElevatedButton.icon(
                      onPressed: _completeOnboarding,
                      icon: const Icon(Icons.rocket_launch),
                      label: const Text('Get Started'),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPage(int index) {
    final page = _pages[index];

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Icon
          Container(
            padding: const EdgeInsets.all(28),
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: page.gradient),
              borderRadius: BorderRadius.circular(28),
              boxShadow: [
                BoxShadow(
                  color: page.gradient[0].withValues(alpha: 0.4),
                  blurRadius: 30, offset: const Offset(0, 12),
                ),
              ],
            ),
            child: Icon(page.icon, size: 56, color: Colors.white),
          ),
          const SizedBox(height: 32),

          Text(
            page.title,
            style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            page.subtitle,
            style: TextStyle(fontSize: 16, color: AppTheme.accent, fontWeight: FontWeight.w600),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            page.description,
            style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary, height: 1.6),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),

          // Permission buttons per page
          if (index == 1) ...[
            _permissionButton(
              'SMS Permission',
              _smsGranted,
              _requestSmsPermission,
              Icons.sms,
            ),
          ],
          if (index == 2) ...[
            _permissionButton(
              'Push Notifications',
              _notifGranted,
              _requestNotificationPermission,
              Icons.notifications,
            ),
            const SizedBox(height: 12),
            _permissionButton(
              'Notification Access',
              _notifListenerGranted,
              () async {
                await _openNotificationListenerSettings();
                // Check again after user returns
                Future.delayed(const Duration(seconds: 2), _checkPermissions);
              },
              Icons.app_settings_alt,
            ),
          ],
          if (index == 3) ...[
            _statusRow('SMS Monitoring', _smsGranted),
            _statusRow('Notification Access', _notifListenerGranted),
          ],
        ],
      ),
    );
  }

  Widget _permissionButton(String label, bool granted, VoidCallback onTap, IconData icon) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: granted ? null : onTap,
        icon: Icon(granted ? Icons.check_circle : icon,
            color: granted ? AppTheme.success : AppTheme.accent),
        label: Text(
          granted ? '$label — Granted ✓' : 'Enable $label',
          style: TextStyle(color: granted ? AppTheme.success : AppTheme.accent),
        ),
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 14),
          side: BorderSide(color: granted ? AppTheme.success.withValues(alpha: 0.3) : AppTheme.accent),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
    );
  }

  Widget _statusRow(String label, bool active) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(active ? Icons.check_circle : Icons.cancel,
              color: active ? AppTheme.success : AppTheme.textSecondary, size: 20),
          const SizedBox(width: 8),
          Text(label, style: TextStyle(
            color: active ? AppTheme.success : AppTheme.textSecondary,
            fontWeight: FontWeight.w600,
          )),
        ],
      ),
    );
  }
}

class _PageData {
  final IconData icon;
  final List<Color> gradient;
  final String title;
  final String subtitle;
  final String description;

  const _PageData({
    required this.icon,
    required this.gradient,
    required this.title,
    required this.subtitle,
    required this.description,
  });
}
