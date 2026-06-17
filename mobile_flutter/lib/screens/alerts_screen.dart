/// Alerts Screen — View and acknowledge real-time threat alerts
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../config/theme.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  List<dynamic> _alerts = [];
  int _total = 0;
  bool _loading = true;
  bool _showUnacknowledgedOnly = false;

  @override
  void initState() {
    super.initState();
    _fetchAlerts();
  }

  Future<void> _fetchAlerts() async {
    final auth = context.read<AuthService>();
    if (auth.token == null) return;

    setState(() => _loading = true);
    try {
      final api = ApiService(auth.token!);
      final data = await api.getAlerts(
        limit: 50,
        unacknowledgedOnly: _showUnacknowledgedOnly,
      );
      if (mounted) {
        setState(() {
          _alerts = data['alerts'] ?? [];
          _total = data['total'] ?? 0;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _acknowledge(String alertId) async {
    final auth = context.read<AuthService>();
    if (auth.token == null) return;

    try {
      final api = ApiService(auth.token!);
      await api.acknowledgeAlert(alertId);
      _fetchAlerts();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ALERTS'),
        actions: [
          IconButton(
            icon: Icon(
              _showUnacknowledgedOnly ? Icons.filter_alt : Icons.filter_alt_outlined,
              color: _showUnacknowledgedOnly ? AppTheme.accent : null,
            ),
            onPressed: () {
              setState(() => _showUnacknowledgedOnly = !_showUnacknowledgedOnly);
              _fetchAlerts();
            },
            tooltip: 'Toggle unacknowledged only',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchAlerts,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _alerts.isEmpty
                ? ListView(children: [
                    const SizedBox(height: 100),
                    Icon(Icons.notifications_none, size: 64, color: AppTheme.success.withOpacity(0.4)),
                    const SizedBox(height: 16),
                    const Center(child: Text('No alerts', style: TextStyle(color: AppTheme.textSecondary, fontSize: 16))),
                  ])
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _alerts.length,
                    itemBuilder: (context, i) => _buildAlertCard(_alerts[i]),
                  ),
      ),
    );
  }

  Widget _buildAlertCard(dynamic alert) {
    final severity = (alert['severity'] ?? 'info').toString();
    final title = alert['title'] ?? 'Alert';
    final description = alert['description'] ?? '';
    final acknowledged = alert['acknowledged'] == true;
    final alertId = alert['id']?.toString() ?? '';
    final createdAt = alert['created_at'] ?? '';

    Color severityColor;
    IconData severityIcon;
    switch (severity) {
      case 'critical':
        severityColor = AppTheme.critical;
        severityIcon = Icons.error;
        break;
      case 'high':
        severityColor = AppTheme.danger;
        severityIcon = Icons.warning_amber;
        break;
      case 'warning':
        severityColor = AppTheme.warning;
        severityIcon = Icons.info_outline;
        break;
      default:
        severityColor = AppTheme.accent;
        severityIcon = Icons.info;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: acknowledged ? AppTheme.border : severityColor.withOpacity(0.4),
          width: acknowledged ? 1 : 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: severityColor.withOpacity(0.08),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(15)),
            ),
            child: Row(
              children: [
                Icon(severityIcon, color: severityColor, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    severity.toUpperCase(),
                    style: TextStyle(
                      color: severityColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                      letterSpacing: 1,
                    ),
                  ),
                ),
                if (acknowledged)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppTheme.success.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text('ACK', style: TextStyle(color: AppTheme.success, fontSize: 10, fontWeight: FontWeight.bold)),
                  ),
              ],
            ),
          ),

          // Body
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 6),
                Text(description, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      createdAt.length > 16 ? createdAt.substring(0, 16).replaceAll('T', ' ') : createdAt,
                      style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                    ),
                    if (!acknowledged)
                      TextButton.icon(
                        onPressed: () => _acknowledge(alertId),
                        icon: const Icon(Icons.check_circle, size: 16),
                        label: const Text('Acknowledge', style: TextStyle(fontSize: 12)),
                        style: TextButton.styleFrom(foregroundColor: AppTheme.success),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
