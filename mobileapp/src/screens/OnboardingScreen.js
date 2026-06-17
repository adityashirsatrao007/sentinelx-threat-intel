import React, { useContext, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ScrollView } from 'react-native';
import { AuthContext } from '../context/AuthContext';
import * as BackgroundFetch from 'expo-background-fetch';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

const BACKGROUND_MONITOR_TASK = 'BACKGROUND_MONITOR_TASK';

export default function OnboardingScreen() {
  const { completeOnboarding } = useContext(AuthContext);
  const [permissionsStatus, setPermissionsStatus] = useState({
    notifications: false,
    background: false,
    gmail: false,
  });

  const requestNotificationPermission = async () => {
    Alert.alert(
      'Notification Access',
      'Enable SentinelX in your device Notification Settings to monitor WhatsApp, Telegram & Banking alerts.',
      [
        { text: 'Got it', onPress: () => setPermissionsStatus(prev => ({ ...prev, notifications: true })) },
        { text: 'Cancel', style: 'cancel' }
      ]
    );
  };

  const requestBackgroundPermission = async () => {
    try {
      await BackgroundFetch.registerTaskAsync(BACKGROUND_MONITOR_TASK, {
        minimumInterval: 15 * 60,
        stopOnTerminate: false,
        startOnBoot: true,
      });
    } catch (err) {
      // Already registered or Expo Go restriction — still continue
    }
    setPermissionsStatus(prev => ({ ...prev, background: true }));
  };

  const connectGmail = async () => {
    Alert.alert('Connect Gmail', 'Redirecting to Google for Gmail read access...', [
      { text: 'Authorize', onPress: () => setPermissionsStatus(prev => ({ ...prev, gmail: true })) }
    ]);
  };

  const allGranted = permissionsStatus.notifications && permissionsStatus.background && permissionsStatus.gmail;

  return (
    <LinearGradient colors={['#020617', '#0f172a']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Ionicons name="shield-half" size={44} color="#38bdf8" />
          <Text style={styles.title}>Activate Protection</Text>
          <Text style={styles.subtitle}>
            Grant these permissions so SentinelX can monitor threats in real-time across your apps.
          </Text>
        </View>

        <PermissionItem
          icon="notifications-circle-outline"
          title="App Notifications"
          description="Monitor WhatsApp, Telegram & Banking alerts"
          granted={permissionsStatus.notifications}
          onPress={requestNotificationPermission}
        />
        <PermissionItem
          icon="hardware-chip-outline"
          title="Background Execution"
          description="Continuous monitoring while app is closed"
          granted={permissionsStatus.background}
          onPress={requestBackgroundPermission}
        />
        <PermissionItem
          icon="mail-unread-outline"
          title="Gmail Integration"
          description="API-level scan of incoming phishing emails"
          granted={permissionsStatus.gmail}
          onPress={connectGmail}
        />

        <TouchableOpacity
          style={[styles.continueButton, !allGranted && styles.disabledButton]}
          onPress={completeOnboarding}
          disabled={!allGranted}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={allGranted ? ['#3b82f6', '#1d4ed8'] : ['#1e293b', '#0f172a']}
            style={styles.gradientButton}
          >
            <Text style={[styles.continueText, !allGranted && { color: '#475569' }]}>
              {allGranted ? 'Launch Dashboard' : 'Complete All Permissions'}
            </Text>
            {allGranted && <Ionicons name="arrow-forward" size={20} color="#fff" style={{ marginLeft: 10 }} />}
          </LinearGradient>
        </TouchableOpacity>
      </ScrollView>
    </LinearGradient>
  );
}

const PermissionItem = ({ icon, title, description, granted, onPress }) => (
  <TouchableOpacity
    style={[styles.permissionCard, granted && styles.permissionCardGranted]}
    onPress={onPress}
    disabled={granted}
    activeOpacity={0.7}
  >
    <View style={[styles.iconBox, granted && styles.iconBoxGranted]}>
      <Ionicons name={icon} size={26} color={granted ? '#10b981' : '#3b82f6'} />
    </View>
    <View style={styles.permissionTextContainer}>
      <Text style={styles.permissionTitle}>{title}</Text>
      <Text style={styles.permissionDesc}>{description}</Text>
    </View>
    {granted ? (
      <Ionicons name="checkmark-circle" size={28} color="#10b981" />
    ) : (
      <View style={styles.statusBadge}>
        <Text style={styles.statusText}>Grant</Text>
      </View>
    )}
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 24, paddingTop: 80, paddingBottom: 60 },
  header: { marginBottom: 36 },
  title: { fontSize: 30, fontWeight: '900', color: '#f8fafc', marginTop: 14, marginBottom: 10, letterSpacing: -0.5 },
  subtitle: { fontSize: 15, color: '#94a3b8', lineHeight: 22 },
  permissionCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.03)', padding: 16,
    borderRadius: 16, marginBottom: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.05)',
  },
  permissionCardGranted: {
    backgroundColor: 'rgba(16, 185, 129, 0.05)',
    borderColor: 'rgba(16, 185, 129, 0.2)',
  },
  iconBox: {
    width: 50, height: 50, borderRadius: 12,
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    justifyContent: 'center', alignItems: 'center', marginRight: 14,
  },
  iconBoxGranted: { backgroundColor: 'rgba(16, 185, 129, 0.1)' },
  permissionTextContainer: { flex: 1, marginRight: 10 },
  permissionTitle: { fontSize: 16, fontWeight: '700', color: '#f8fafc', marginBottom: 4 },
  permissionDesc: { fontSize: 13, color: '#94a3b8', lineHeight: 18 },
  statusBadge: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20,
  },
  statusText: { color: '#ffffff', fontWeight: '700', fontSize: 13 },
  continueButton: { marginTop: 10, borderRadius: 100, overflow: 'hidden' },
  disabledButton: { opacity: 0.5 },
  gradientButton: {
    flexDirection: 'row', padding: 18,
    justifyContent: 'center', alignItems: 'center',
  },
  continueText: { color: '#ffffff', fontSize: 17, fontWeight: '800' },
});
