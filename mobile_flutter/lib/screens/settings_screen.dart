/// Settings Screen — User profile, monitoring controls, Email integration, connection status
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:http/http.dart' as http;
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/sms_service.dart';
import '../config/api_config.dart';
import '../config/theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _backendOnline = false;
  bool _checkingHealth = true;
  List<Map<String, dynamic>> _emailAccounts = [];
  bool _loadingEmail = false;
  bool _scanning = false;

  @override
  void initState() {
    super.initState();
    _checkBackend();
    _fetchEmailAccounts();
  }

  Future<void> _checkBackend() async {
    setState(() => _checkingHealth = true);
    final auth = context.read<AuthService>();
    if (auth.token != null) {
      final api = ApiService(auth.token!);
      final online = await api.checkHealth();
      if (mounted) setState(() {
        _backendOnline = online;
        _checkingHealth = false;
      });
    } else {
      if (mounted) setState(() => _checkingHealth = false);
    }
  }

  Future<void> _fetchEmailAccounts() async {
    final auth = context.read<AuthService>();
    if (auth.token == null) return;
    setState(() => _loadingEmail = true);
    try {
      final resp = await http.get(
        Uri.parse(ApiConfig.emailAccounts),
        headers: auth.authHeaders,
      );
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        if (mounted) setState(() => _emailAccounts = List<Map<String, dynamic>>.from(data));
      }
    } catch (e) {
      debugPrint('Failed to fetch email accounts: $e');
    } finally {
      if (mounted) setState(() => _loadingEmail = false);
    }
  }

  Future<void> _connectEmail(String email, String appPassword) async {
    final auth = context.read<AuthService>();
    if (auth.token == null) return;

    try {
      final resp = await http.post(
        Uri.parse(ApiConfig.emailConnect),
        headers: auth.authHeaders,
        body: jsonEncode({
          'email_address': email,
          'app_password': appPassword,
        }),
      );

      if (mounted) {
        if (resp.statusCode == 200) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('✅ Gmail connected! Emails will be scanned automatically.'), backgroundColor: AppTheme.success),
          );
          _fetchEmailAccounts();
        } else {
          final err = jsonDecode(resp.body);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(err['detail'] ?? 'Connection failed'), backgroundColor: AppTheme.danger),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.danger),
        );
      }
    }
  }

  Future<void> _scanNow() async {
    final auth = context.read<AuthService>();
    if (auth.token == null) return;
    setState(() => _scanning = true);

    try {
      final resp = await http.post(
        Uri.parse(ApiConfig.emailScan),
        headers: auth.authHeaders,
      );
      if (mounted) {
        if (resp.statusCode == 200) {
          final data = jsonDecode(resp.body);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Scanned ${data['emails_scanned']} emails — ${data['threats_found']} threats found'),
              backgroundColor: data['threats_found'] > 0 ? AppTheme.warning : AppTheme.success,
            ),
          );
          _fetchEmailAccounts(); // refresh sync time
        } else {
          final err = jsonDecode(resp.body);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(err['detail'] ?? 'Scan failed'), backgroundColor: AppTheme.danger),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Scan error: $e'), backgroundColor: AppTheme.danger),
        );
      }
    } finally {
      if (mounted) setState(() => _scanning = false);
    }
  }

  Future<void> _disconnectEmail(String accountId) async {
    final auth = context.read<AuthService>();
    if (auth.token == null) return;

    try {
      final resp = await http.delete(
        Uri.parse('${ApiConfig.emailAccounts}/$accountId'),
        headers: auth.authHeaders,
      );
      if (resp.statusCode == 200) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Email disconnected'), backgroundColor: AppTheme.success),
          );
        }
        _fetchEmailAccounts();
      }
    } catch (e) {
      debugPrint('Failed to disconnect: $e');
    }
  }

  void _showConnectDialog() {
    final emailCtrl = TextEditingController();
    final passCtrl = TextEditingController();
    bool connecting = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          backgroundColor: AppTheme.surface,
          title: const Row(
            children: [
              Icon(Icons.email, color: AppTheme.accent),
              SizedBox(width: 8),
              Text('Connect Gmail'),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.accent.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('How to get App Password:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                      SizedBox(height: 4),
                      Text('1. Go to myaccount.google.com', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      Text('2. Security → 2-Step Verification', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      Text('3. App Passwords → Generate', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                      Text('4. Select "Mail" → Copy the password', style: TextStyle(fontSize: 11, color: AppTheme.textSecondary)),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                GestureDetector(
                  onTap: () => launchUrl(
                    Uri.parse('https://myaccount.google.com/apppasswords'),
                    mode: LaunchMode.externalApplication,
                  ),
                  child: const Text(
                    'Open Google App Passwords →',
                    style: TextStyle(color: AppTheme.accent, fontSize: 12, fontWeight: FontWeight.bold, decoration: TextDecoration.underline),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Gmail Address',
                    hintText: 'you@gmail.com',
                    prefixIcon: Icon(Icons.email_outlined, size: 20),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: passCtrl,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'App Password',
                    hintText: 'xxxx xxxx xxxx xxxx',
                    prefixIcon: Icon(Icons.key, size: 20),
                    isDense: true,
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: connecting ? null : () async {
                if (emailCtrl.text.isEmpty || passCtrl.text.isEmpty) return;
                setDialogState(() => connecting = true);
                await _connectEmail(emailCtrl.text.trim(), passCtrl.text.trim());
                if (ctx.mounted) Navigator.pop(ctx);
              },
              child: connecting
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Connect'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final sms = context.watch<SmsMonitorService>();

    return Scaffold(
      appBar: AppBar(title: const Text('SETTINGS')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ─── User Profile ────────────────────────────────────────
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: AppTheme.accent,
                  child: Text(
                    (auth.userName.isNotEmpty ? auth.userName[0] : 'U').toUpperCase(),
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(auth.userName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      Text(auth.userEmail, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppTheme.accent.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          auth.userRole.toUpperCase(),
                          style: const TextStyle(color: AppTheme.accent, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ─── Connection Status ───────────────────────────────────
          _sectionTitle('Connection'),
          _settingTile(
            icon: Icons.cloud,
            title: 'Backend Server',
            subtitle: ApiConfig.baseUrl,
            trailing: _checkingHealth
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : Icon(
                    _backendOnline ? Icons.check_circle : Icons.cancel,
                    color: _backendOnline ? AppTheme.success : AppTheme.danger,
                  ),
            onTap: _checkBackend,
          ),
          const SizedBox(height: 20),

          // ─── Monitoring ──────────────────────────────────────────
          _sectionTitle('Monitoring'),
          _settingTile(
            icon: Icons.sms,
            title: 'SMS Monitoring',
            subtitle: sms.isMonitoring
                ? '${sms.interceptedMessages.length} messages scanned'
                : 'Tap to enable',
            trailing: Switch(
              value: sms.isMonitoring,
              activeColor: AppTheme.success,
              onChanged: (val) async {
                if (val) {
                  if (auth.token != null) {
                    sms.setApiService(ApiService(auth.token!));
                  }
                  await sms.startMonitoring();
                } else {
                  sms.stopMonitoring();
                }
              },
            ),
          ),
          _settingTile(
            icon: Icons.notifications_active,
            title: 'Threat Notifications',
            subtitle: 'Local alerts on threat detection',
            trailing: const Icon(Icons.check_circle, color: AppTheme.success),
          ),
          const SizedBox(height: 20),

          // ─── Email Integration ────────────────────────────────────
          _sectionTitle('Email Integration'),
          if (_loadingEmail)
            const Center(child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(strokeWidth: 2),
            ))
          else if (_emailAccounts.isEmpty)
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppTheme.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.accent.withOpacity(0.2)),
              ),
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppTheme.accent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Icon(Icons.email, size: 36, color: AppTheme.accent),
                  ),
                  const SizedBox(height: 16),
                  const Text('Connect Gmail', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  const Text(
                    'Scan incoming emails for phishing threats.\nJust need your email + a Google App Password.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _showConnectDialog,
                      icon: const Icon(Icons.link, size: 18),
                      label: const Text('Connect Gmail Account'),
                      style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
                    ),
                  ),
                ],
              ),
            )
          else ...[
            ..._emailAccounts.map((account) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.surface,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppTheme.success.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.email, color: AppTheme.success, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          account['email_address'] ?? '',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          account['last_synced_at'] != null
                              ? 'Last scan: ${_formatDate(account['last_synced_at'])}'
                              : 'Connected — ready to scan',
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.link_off, color: AppTheme.danger, size: 20),
                    onPressed: () => _showDisconnectDialog(account['id'], account['email_address'] ?? ''),
                  ),
                ],
              ),
            )),
            // Scan Now button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _scanning ? null : _scanNow,
                icon: _scanning
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.radar, size: 18),
                label: Text(_scanning ? 'Scanning...' : 'Scan Emails Now'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  side: const BorderSide(color: AppTheme.accent),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
            const SizedBox(height: 4),
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: TextButton.icon(
                onPressed: _showConnectDialog,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Add Another Account', style: TextStyle(fontSize: 12)),
              ),
            ),
          ],
          const SizedBox(height: 20),

          // ─── Info ────────────────────────────────────────────────
          _sectionTitle('About'),
          _settingTile(
            icon: Icons.info_outline,
            title: 'SentinelX',
            subtitle: 'v1.0.0 — AI-Powered Threat Detection',
          ),
          const SizedBox(height: 32),

          // ─── Logout ──────────────────────────────────────────────
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () async {
                sms.stopMonitoring();
                await auth.logout();
              },
              icon: const Icon(Icons.logout, color: AppTheme.danger),
              label: const Text('Sign Out', style: TextStyle(color: AppTheme.danger)),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                side: BorderSide(color: AppTheme.danger.withOpacity(0.3)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showDisconnectDialog(String id, String email) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Disconnect Email?'),
        content: Text('Stop scanning $email for threats?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              _disconnectEmail(id);
            },
            child: const Text('Disconnect', style: TextStyle(color: AppTheme.danger)),
          ),
        ],
      ),
    );
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso);
      final diff = DateTime.now().difference(dt);
      if (diff.inMinutes < 1) return 'Just now';
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      if (diff.inHours < 24) return '${diff.inHours}h ago';
      return '${diff.inDays}d ago';
    } catch (_) {
      return iso;
    }
  }

  Widget _sectionTitle(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(text, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textSecondary, letterSpacing: 1)),
    );
  }

  Widget _settingTile({
    required IconData icon,
    required String title,
    String? subtitle,
    Widget? trailing,
    VoidCallback? onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListTile(
        leading: Icon(icon, color: AppTheme.accent),
        title: Text(title, style: const TextStyle(fontSize: 15)),
        subtitle: subtitle != null ? Text(subtitle, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)) : null,
        trailing: trailing,
        onTap: onTap,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
