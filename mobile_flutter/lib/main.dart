/// SentinelX — AI-Powered Threat Detection Mobile App
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config/theme.dart';
import 'services/auth_service.dart';
import 'services/sms_service.dart';
import 'services/notification_service.dart';
import 'services/notification_monitor_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/alerts_screen.dart';
import 'screens/analyze_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/onboarding_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService.initialize();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => SmsMonitorService()),
        ChangeNotifierProvider(create: (_) => NotificationMonitorService()),
      ],
      child: const SentinelXApp(),
    ),
  );
}

class SentinelXApp extends StatefulWidget {
  const SentinelXApp({super.key});

  @override
  State<SentinelXApp> createState() => _SentinelXAppState();
}

class _SentinelXAppState extends State<SentinelXApp> {
  bool _initialized = false;
  bool _needsOnboarding = true;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final prefs = await SharedPreferences.getInstance();
    _needsOnboarding = !(prefs.getBool('onboarding_complete') ?? false);
    final auth = context.read<AuthService>();
    await auth.tryAutoLogin();
    setState(() => _initialized = true);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SentinelX',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: _initialized
          ? Consumer<AuthService>(
              builder: (context, auth, _) {
                if (!auth.isLoggedIn) return const LoginScreen();
                if (_needsOnboarding) {
                  return OnboardingScreen(
                    onComplete: () => setState(() => _needsOnboarding = false),
                  );
                }
                return const MainNavigation();
              },
            )
          : const _SplashScreen(),
    );
  }
}

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _currentIndex = 0;

  final _screens = const [
    DashboardScreen(),
    AlertsScreen(),
    AnalyzeScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _screens),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: AppTheme.border, width: 0.5)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (i) => setState(() => _currentIndex = i),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
            BottomNavigationBarItem(icon: Icon(Icons.notifications_active), label: 'Alerts'),
            BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Analyze'),
            BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
          ],
        ),
      ),
    );
  }
}

class _SplashScreen extends StatelessWidget {
  const _SplashScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [AppTheme.accent, Color(0xFF8B5CF6)]),
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Icon(Icons.shield, size: 48, color: Colors.white),
            ),
            const SizedBox(height: 24),
            const Text('SENTINEL X',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 4, color: Colors.white)),
            const SizedBox(height: 32),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
