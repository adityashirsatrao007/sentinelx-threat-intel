/// Analyze Screen — Manually submit SMS/Email for threat analysis
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/notification_service.dart';
import '../config/theme.dart';

class AnalyzeScreen extends StatefulWidget {
  const AnalyzeScreen({super.key});

  @override
  State<AnalyzeScreen> createState() => _AnalyzeScreenState();
}

class _AnalyzeScreenState extends State<AnalyzeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;

  // SMS fields
  final _smsSenderCtrl = TextEditingController();
  final _smsMessageCtrl = TextEditingController();

  // Email fields
  final _emailSenderCtrl = TextEditingController();
  final _emailSubjectCtrl = TextEditingController();
  final _emailBodyCtrl = TextEditingController();

  Map<String, dynamic>? _result;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    _smsSenderCtrl.dispose();
    _smsMessageCtrl.dispose();
    _emailSenderCtrl.dispose();
    _emailSubjectCtrl.dispose();
    _emailBodyCtrl.dispose();
    super.dispose();
  }

  Future<void> _analyzeSms() async {
    if (_smsMessageCtrl.text.isEmpty) return;
    await _runAnalysis(() async {
      final auth = context.read<AuthService>();
      final api = ApiService(auth.token!);
      return api.analyzeSms(_smsSenderCtrl.text.trim(), _smsMessageCtrl.text.trim());
    });
  }

  Future<void> _analyzeEmail() async {
    if (_emailBodyCtrl.text.isEmpty) return;
    await _runAnalysis(() async {
      final auth = context.read<AuthService>();
      final api = ApiService(auth.token!);
      return api.analyzeEmail(
        _emailSenderCtrl.text.trim(),
        _emailSubjectCtrl.text.trim(),
        _emailBodyCtrl.text.trim(),
      );
    });
  }

  Future<void> _runAnalysis(Future<Map<String, dynamic>> Function() analyzer) async {
    setState(() {
      _loading = true;
      _result = null;
    });

    try {
      final result = await analyzer();
      setState(() {
        _result = result;
        _loading = false;
      });

      // Show local notification if threat detected
      final risk = (result['risk_score'] ?? 0.0).toDouble();
      if (result['threat_detected'] == true) {
        NotificationService.showThreatAlert(
          title: '⚠️ ${result['threat_level']} Threat Detected',
          body: 'Risk: ${risk.toStringAsFixed(1)}/10 — ${(result['reasons'] as List?)?.first ?? 'Suspicious content detected'}',
          riskScore: risk,
        );
      }
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ANALYZE'),
        bottom: TabBar(
          controller: _tabCtrl,
          indicatorColor: AppTheme.accent,
          tabs: const [
            Tab(icon: Icon(Icons.sms), text: 'SMS'),
            Tab(icon: Icon(Icons.email), text: 'Email'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabCtrl,
        children: [
          _buildSmsTab(),
          _buildEmailTab(),
        ],
      ),
    );
  }

  Widget _buildSmsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            controller: _smsSenderCtrl,
            decoration: const InputDecoration(
              labelText: 'Sender (phone number)',
              prefixIcon: Icon(Icons.phone),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _smsMessageCtrl,
            maxLines: 5,
            decoration: const InputDecoration(
              labelText: 'SMS Message',
              prefixIcon: Icon(Icons.message),
              alignLabelWithHint: true,
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _loading ? null : _analyzeSms,
            icon: _loading
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.search),
            label: const Text('Analyze SMS'),
          ),
          const SizedBox(height: 20),
          if (_result != null) _buildResultCard(),
        ],
      ),
    );
  }

  Widget _buildEmailTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            controller: _emailSenderCtrl,
            decoration: const InputDecoration(
              labelText: 'Sender email',
              prefixIcon: Icon(Icons.person),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _emailSubjectCtrl,
            decoration: const InputDecoration(
              labelText: 'Subject',
              prefixIcon: Icon(Icons.subject),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _emailBodyCtrl,
            maxLines: 6,
            decoration: const InputDecoration(
              labelText: 'Email Body',
              prefixIcon: Icon(Icons.article),
              alignLabelWithHint: true,
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _loading ? null : _analyzeEmail,
            icon: _loading
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.search),
            label: const Text('Analyze Email'),
          ),
          const SizedBox(height: 20),
          if (_result != null) _buildResultCard(),
        ],
      ),
    );
  }

  Widget _buildResultCard() {
    final risk = (_result!['risk_score'] ?? 0.0).toDouble();
    final color = AppTheme.riskColor(risk);
    final detected = _result!['threat_detected'] == true;
    final reasons = (_result!['reasons'] as List?)?.cast<String>() ?? [];

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.5), width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Icon(detected ? Icons.warning_amber : Icons.check_circle, color: color, size: 32),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      detected ? 'THREAT DETECTED' : 'SAFE',
                      style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1),
                    ),
                    Text(
                      '${_result!['threat_level']} — ${_result!['classification_label']}',
                      style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                    ),
                  ],
                ),
              ),
              // Risk score
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${risk.toStringAsFixed(1)}/10',
                  style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 20),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Score breakdown
          _scoreRow('NLP', (_result!['nlp_score'] ?? 0.0).toDouble()),
          _scoreRow('Behavior', (_result!['behavior_score'] ?? 0.0).toDouble()),
          _scoreRow('URL', (_result!['url_score'] ?? 0.0).toDouble()),
          _scoreRow('Reputation', (_result!['reputation_score'] ?? 0.0).toDouble()),

          if (reasons.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text('Indicators:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            const SizedBox(height: 6),
            ...reasons.map((r) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.arrow_right, size: 16, color: color),
                      const SizedBox(width: 4),
                      Expanded(child: Text(r, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary))),
                    ],
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _scoreRow(String label, double value) {
    final normalized = value.clamp(0.0, 10.0) / 10.0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          SizedBox(width: 80, child: Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary))),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: normalized,
                backgroundColor: AppTheme.surfaceLight,
                valueColor: AlwaysStoppedAnimation(AppTheme.riskColor(value)),
                minHeight: 6,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(value.toStringAsFixed(1), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
