/// Dashboard Screen — Real-time threat monitoring overview
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/sms_service.dart';
import '../services/notification_monitor_service.dart';
import '../config/theme.dart';
import 'threat_detail_screen.dart';
import 'dart:async';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic> _stats = {};
  List<dynamic> _threats = [];
  bool _isLoading = true;
  bool _backendOnline = false;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _fetchData();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) => _fetchData());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchData() async {
    final auth = context.read<AuthService>();
    if (auth.token == null) return;

    final api = ApiService(auth.token!);

    try {
      final online = await api.checkHealth();
      final stats = await api.getStats();
      final threats = await api.getThreats(limit: 10);

      if (mounted) {
        setState(() {
          _backendOnline = online;
          _stats = stats;
          _threats = threats;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _backendOnline = false;
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final sms = context.watch<SmsMonitorService>();
    final notifMon = context.watch<NotificationMonitorService>();

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _fetchData,
        child: CustomScrollView(
          slivers: [
            // ─── App Bar ─────────────────────────────────────────────
            SliverAppBar(
              floating: true,
              title: const Text('SENTINEL X'),
              actions: [
                _buildStatusDot(_backendOnline),
                const SizedBox(width: 8),
                _buildStatusDot(sms.isMonitoring, label: 'SMS'),
                const SizedBox(width: 8),
                _buildStatusDot(notifMon.isMonitoring, label: 'Apps'),
                const SizedBox(width: 16),
              ],
            ),

            // ─── Content ─────────────────────────────────────────────
            SliverPadding(
              padding: const EdgeInsets.all(16),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  // Welcome card
                  _buildWelcomeCard(auth),
                  const SizedBox(height: 20),

                  // Stats grid
                  if (!_isLoading) ...[
                    _buildStatsGrid(),
                    const SizedBox(height: 24),

                    // Monitoring cards
                    _buildSmsMonitorCard(sms),
                    const SizedBox(height: 12),
                    _buildNotifMonitorCard(notifMon),
                    const SizedBox(height: 24),

                    // Recent threats
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Recent Threats',
                            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                        Text('${_threats.length} total',
                            style: TextStyle(color: AppTheme.accent, fontWeight: FontWeight.w600)),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ..._threats.map((t) => _buildThreatCard(t)),

                    if (_threats.isEmpty)
                      _buildEmptyState(),
                  ] else
                    const Center(child: Padding(
                      padding: EdgeInsets.all(40),
                      child: CircularProgressIndicator(),
                    )),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusDot(bool active, {String? label}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8, height: 8,
          decoration: BoxDecoration(
            color: active ? AppTheme.success : AppTheme.danger,
            shape: BoxShape.circle,
            boxShadow: [BoxShadow(color: (active ? AppTheme.success : AppTheme.danger).withOpacity(0.5), blurRadius: 6)],
          ),
        ),
        if (label != null) ...[
          const SizedBox(width: 4),
          Text(label, style: TextStyle(fontSize: 10, color: active ? AppTheme.success : AppTheme.textSecondary)),
        ],
      ],
    );
  }

  Widget _buildWelcomeCard(AuthService auth) {
    final isAlert = (_stats['critical_alerts'] ?? 0) > 0;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isAlert
              ? [const Color(0xFFEF4444), const Color(0xFFB91C1C)]
              : [AppTheme.accent, const Color(0xFF7C3AED)],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: (isAlert ? AppTheme.danger : AppTheme.accent).withOpacity(0.3),
            blurRadius: 20, offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(isAlert ? Icons.gpp_maybe : Icons.gpp_good, size: 52, color: Colors.white),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isAlert ? 'Threats Detected!' : 'System Secure',
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const SizedBox(height: 4),
                Text(
                  'Welcome, ${auth.userName}',
                  style: const TextStyle(color: Colors.white70, fontSize: 14),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid() {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.5,
      children: [
        _statCard('Total Threats', '${_stats['total_threats'] ?? 0}', Icons.security, AppTheme.accent),
        _statCard('Phishing', '${_stats['phishing_attempts'] ?? 0}', Icons.phishing, AppTheme.warning),
        _statCard('Critical', '${_stats['critical_alerts'] ?? 0}', Icons.warning_amber, AppTheme.danger),
        _statCard('Avg Risk', '${(_stats['avg_risk_score'] ?? 0.0).toStringAsFixed(1)}', Icons.speed, AppTheme.success),
      ],
    );
  }

  Widget _statCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color, size: 22),
              const SizedBox(width: 8),
              Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
            ],
          ),
          const SizedBox(height: 4),
          Text(title, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildSmsMonitorCard(SmsMonitorService sms) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: sms.isMonitoring ? AppTheme.success.withOpacity(0.3) : AppTheme.border),
      ),
      child: Row(
        children: [
          Icon(
            sms.isMonitoring ? Icons.sms : Icons.sms_failed,
            color: sms.isMonitoring ? AppTheme.success : AppTheme.textSecondary,
            size: 28,
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  sms.isMonitoring ? 'SMS Monitoring Active' : 'SMS Monitoring Off',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
                Text(
                  sms.isMonitoring
                      ? '${sms.interceptedMessages.length} messages scanned'
                      : 'Enable to auto-scan incoming SMS',
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                ),
              ],
            ),
          ),
          Switch(
            value: sms.isMonitoring,
            activeColor: AppTheme.success,
            onChanged: (val) async {
              if (val) {
                final auth = context.read<AuthService>();
                if (auth.token != null) {
                  sms.setApiService(ApiService(auth.token!));
                }
                await sms.startMonitoring();
              } else {
                sms.stopMonitoring();
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildThreatCard(dynamic t) {
    final double risk = (t['risk_score'] ?? 0.0).toDouble();
    final color = AppTheme.riskColor(risk);
    final sender = t['sender'] ?? 'Unknown';
    final riskLabel = AppTheme.riskLabel(risk);
    final classLabel = (t['classification_label'] ?? 'unknown').toString().toUpperCase();
    final label = risk >= 3.1 ? '$riskLabel — $classLabel' : riskLabel;
    final channel = (t['channel'] ?? 'email').toString().toUpperCase();

    return GestureDetector(
      onTap: () => Navigator.push(context,
        MaterialPageRoute(builder: (_) => ThreatDetailScreen(threat: t))),
      child: Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              channel == 'SMS' ? Icons.sms : channel == 'CALL' ? Icons.phone : Icons.email,
              color: color, size: 22,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: color)),
                Text(sender, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12), overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('${risk.toStringAsFixed(1)}', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20, color: color)),
              Text('/10', style: TextStyle(color: AppTheme.textSecondary, fontSize: 10)),
            ],
          ),
          const SizedBox(width: 4),
          Icon(Icons.chevron_right, color: AppTheme.textSecondary, size: 20),
        ],
      ),
    ),
    );
  }

  Widget _buildNotifMonitorCard(NotificationMonitorService notifMon) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: notifMon.isMonitoring ? AppTheme.accent.withOpacity(0.3) : AppTheme.border),
      ),
      child: Row(
        children: [
          Icon(
            notifMon.isMonitoring ? Icons.notifications_active : Icons.notifications_off,
            color: notifMon.isMonitoring ? AppTheme.accent : AppTheme.textSecondary,
            size: 28,
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  notifMon.isMonitoring ? 'App Monitoring Active' : 'App Monitoring Off',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
                Text(
                  notifMon.isMonitoring
                      ? '${notifMon.interceptedNotifications.length} notifications scanned'
                      : 'WhatsApp, Telegram, Banking',
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                ),
              ],
            ),
          ),
          Switch(
            value: notifMon.isMonitoring,
            activeColor: AppTheme.accent,
            onChanged: (val) async {
              if (val) {
                final auth = context.read<AuthService>();
                if (auth.token != null) {
                  notifMon.setApiService(ApiService(auth.token!));
                }
                await notifMon.startMonitoring();
              } else {
                notifMon.stopMonitoring();
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(40),
      child: Column(
        children: [
          Icon(Icons.check_circle_outline, size: 64, color: AppTheme.success.withOpacity(0.5)),
          const SizedBox(height: 16),
          const Text('No threats detected', style: TextStyle(color: AppTheme.textSecondary, fontSize: 16)),
          const Text('All systems are clean', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
        ],
      ),
    );
  }
}
