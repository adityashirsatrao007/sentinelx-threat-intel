/// SentinelX App Theme
import 'package:flutter/material.dart';

class AppTheme {
  // ─── Colors ────────────────────────────────────────────────────────────────
  static const Color bg = Color(0xFF0F172A);
  static const Color surface = Color(0xFF1E293B);
  static const Color surfaceLight = Color(0xFF334155);
  static const Color accent = Color(0xFF3B82F6);
  static const Color accentLight = Color(0xFF60A5FA);
  static const Color success = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color danger = Color(0xFFEF4444);
  static const Color critical = Color(0xFFDC2626);
  static const Color textPrimary = Colors.white;
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color border = Color(0xFF334155);

  static Color riskColor(double score) {
    if (score >= 8.5) return critical;
    if (score >= 6.1) return danger;
    if (score >= 3.1) return warning;
    return success;
  }

  static String riskLabel(double score) {
    if (score >= 8.5) return 'CRITICAL';
    if (score >= 6.1) return 'HIGH';
    if (score >= 3.1) return 'MEDIUM';
    return 'LOW';
  }

  static ThemeData get darkTheme => ThemeData(
        brightness: Brightness.dark,
        primaryColor: accent,
        scaffoldBackgroundColor: bg,
        cardColor: surface,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          elevation: 0,
          centerTitle: false,
          titleTextStyle: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w900,
            letterSpacing: 2,
            color: textPrimary,
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: accent,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: surface,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: border),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: accent, width: 2),
          ),
          labelStyle: const TextStyle(color: textSecondary),
          hintStyle: const TextStyle(color: textSecondary),
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: surface,
          selectedItemColor: accent,
          unselectedItemColor: textSecondary,
          type: BottomNavigationBarType.fixed,
        ),
        textTheme: const TextTheme(
          headlineLarge: TextStyle(fontWeight: FontWeight.bold, color: textPrimary),
          headlineMedium: TextStyle(fontWeight: FontWeight.bold, color: textPrimary),
          bodyLarge: TextStyle(color: textPrimary),
          bodyMedium: TextStyle(color: textSecondary),
        ),
      );
}
