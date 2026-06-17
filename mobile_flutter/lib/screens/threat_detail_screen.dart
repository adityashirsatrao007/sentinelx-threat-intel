/// Threat Detail Screen — Full analysis view when tapping a threat card
import 'package:flutter/material.dart';
import '../config/theme.dart';

class ThreatDetailScreen extends StatelessWidget {
  final Map<String, dynamic> threat;
  const ThreatDetailScreen({super.key, required this.threat});

  @override
  Widget build(BuildContext context) {
    final double risk = (threat['risk_score'] ?? 0.0).toDouble();
    final color = AppTheme.riskColor(risk);
    final label = AppTheme.riskLabel(risk);
    final detected = threat['threat_detected'] == true;
    final reasons = (threat['reasons'] as List?)?.cast<String>() ?? [];
    final sender = threat['sender'] ?? 'Unknown';
    final channel = (threat['channel'] ?? 'email').toString().toUpperCase();
    final classification = threat['classification_label'] ?? 'unknown';
    final createdAt = threat['created_at'] ?? '';

    return Scaffold(
      appBar: AppBar(
        title: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w900, letterSpacing: 2)),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              '${risk.toStringAsFixed(1)}/10',
              style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ─── Status Banner ──────────────────────────────────────
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: detected
                      ? [color, color.withValues(alpha: 0.7)]
                      : [AppTheme.success, AppTheme.success.withValues(alpha: 0.7)],
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  Icon(
                    detected ? Icons.warning_amber_rounded : Icons.check_circle,
                    size: 56, color: Colors.white,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    detected ? 'THREAT DETECTED' : 'NO THREAT',
                    style: const TextStyle(
                      fontSize: 22, fontWeight: FontWeight.w900,
                      color: Colors.white, letterSpacing: 3,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    classification.toString().toUpperCase(),
                    style: const TextStyle(color: Colors.white70, fontSize: 14),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // ─── Sender Info ────────────────────────────────────────
            _infoCard('Source', [
              _infoRow(Icons.person, 'Sender', sender),
              _infoRow(Icons.category, 'Channel', channel),
              if (createdAt.isNotEmpty)
                _infoRow(Icons.access_time, 'Detected',
                    createdAt.length > 16 ? createdAt.substring(0, 16).replaceAll('T', ' ') : createdAt),
            ]),
            const SizedBox(height: 16),

            // ─── Score Breakdown ────────────────────────────────────
            _infoCard('Risk Breakdown', [
              _scoreBar('NLP Score', (threat['nlp_score'] ?? 0.0).toDouble()),
              _scoreBar('Behavior Score', (threat['behavior_score'] ?? 0.0).toDouble()),
              _scoreBar('URL Score', (threat['url_score'] ?? 0.0).toDouble()),
              _scoreBar('Reputation', (threat['reputation_score'] ?? 0.0).toDouble()),
              const Divider(color: AppTheme.border, height: 24),
              _scoreBar('Final Risk Score', risk, isFinal: true),
            ]),
            const SizedBox(height: 16),

            // ─── Threat Indicators ──────────────────────────────────
            if (reasons.isNotEmpty) ...[
              _infoCard('Threat Indicators', [
                ...reasons.map((r) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        margin: const EdgeInsets.only(top: 4),
                        width: 6, height: 6,
                        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(r, style: const TextStyle(fontSize: 14, height: 1.4)),
                      ),
                    ],
                  ),
                )),
              ]),
              const SizedBox(height: 16),
            ],

            // ─── Suspicious URLs ────────────────────────────────────
            if (threat['suspicious_urls'] != null &&
                (threat['suspicious_urls'] as List).isNotEmpty) ...[
              _infoCard('Suspicious URLs', [
                ...(threat['suspicious_urls'] as List).map((url) => Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.danger.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.danger.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.link_off, color: AppTheme.danger, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          url.toString(),
                          style: const TextStyle(fontSize: 12, color: AppTheme.danger),
                          overflow: TextOverflow.ellipsis,
                          maxLines: 2,
                        ),
                      ),
                    ],
                  ),
                )),
              ]),
              const SizedBox(height: 16),
            ],

            // ─── Behavioral Tactics ─────────────────────────────────
            if (threat['tactics'] != null &&
                (threat['tactics'] as List).isNotEmpty) ...[
              _infoCard('Social Engineering Tactics', [
                Wrap(
                  spacing: 8, runSpacing: 8,
                  children: (threat['tactics'] as List).map((t) => Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppTheme.warning.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppTheme.warning.withValues(alpha: 0.3)),
                    ),
                    child: Text(
                      t.toString().toUpperCase(),
                      style: const TextStyle(
                        color: AppTheme.warning, fontSize: 11,
                        fontWeight: FontWeight.bold, letterSpacing: 0.5,
                      ),
                    ),
                  )).toList(),
                ),
              ]),
              const SizedBox(height: 16),
            ],

            // ─── Raw Content ────────────────────────────────────────
            if (threat['content'] != null || threat['subject'] != null)
              _infoCard('Original Content', [
                if (threat['subject'] != null) ...[
                  Text('Subject', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                  const SizedBox(height: 4),
                  Text(threat['subject'].toString(), style: const TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                ],
                if (threat['content'] != null) ...[
                  Text('Body', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                  const SizedBox(height: 4),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.bg,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      threat['content'].toString(),
                      style: const TextStyle(fontSize: 13, height: 1.5),
                    ),
                  ),
                ],
              ]),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _infoCard(String title, List<Widget> children) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(
            fontSize: 13, fontWeight: FontWeight.bold,
            color: AppTheme.textSecondary, letterSpacing: 1,
          )),
          const SizedBox(height: 12),
          ...children,
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppTheme.textSecondary),
          const SizedBox(width: 8),
          Text('$label: ', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))),
        ],
      ),
    );
  }

  Widget _scoreBar(String label, double value, {bool isFinal = false}) {
    final normalized = value.clamp(0.0, 10.0) / 10.0;
    final barColor = AppTheme.riskColor(value);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: TextStyle(
                fontSize: isFinal ? 14 : 13,
                color: isFinal ? Colors.white : AppTheme.textSecondary,
                fontWeight: isFinal ? FontWeight.bold : FontWeight.normal,
              )),
              Text(
                value.toStringAsFixed(1),
                style: TextStyle(
                  fontSize: isFinal ? 18 : 14,
                  fontWeight: FontWeight.bold,
                  color: barColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: normalized,
              backgroundColor: AppTheme.surfaceLight,
              valueColor: AlwaysStoppedAnimation(barColor),
              minHeight: isFinal ? 8 : 6,
            ),
          ),
        ],
      ),
    );
  }
}
