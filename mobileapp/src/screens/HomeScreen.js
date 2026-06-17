import React, { useContext, useEffect } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, RefreshControl, ScrollView
} from 'react-native';
import { AuthContext } from '../context/AuthContext';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardAPI, alertsAPI } from '../services/api';
import { registerBackgroundTasks } from '../services/backgroundTasks';

export default function HomeScreen() {
  const { logout, user } = useContext(AuthContext);
  const queryClient = useQueryClient();

  useEffect(() => {
    registerBackgroundTasks();
  }, []);

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const res = await dashboardAPI.getStats();
      return res.data;
    },
    refetchInterval: 30000, // auto-refresh every 30 seconds
  });

  const { data: threatsData, isLoading: threatsLoading, refetch: refetchThreats, isRefetching } = useQuery({
    queryKey: ['dashboard-threats'],
    queryFn: async () => {
      const res = await dashboardAPI.getThreats(0, 20);
      return res.data;
    },
    refetchInterval: 30000,
  });

  const { data: alertsData } = useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const res = await alertsAPI.list(false);
      return res.data;
    },
    refetchInterval: 30000,
  });

  const ackMutation = useMutation({
    mutationFn: (alertId) => alertsAPI.acknowledge(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });

  const ackAllMutation = useMutation({
    mutationFn: () => alertsAPI.acknowledgeAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });

  const threats = threatsData?.threats || [];
  const alerts = alertsData?.alerts || [];
  const unackCount = alerts.filter(a => !a.is_acknowledged).length;

  const renderStatCard = (label, value, icon, color) => (
    <View style={styles.statCard} key={label}>
      <View style={[styles.statIconBox, { backgroundColor: `${color}20` }]}>
        <Ionicons name={icon} size={22} color={color} />
      </View>
      <Text style={styles.statValue}>{value ?? '—'}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );

  const renderThreat = ({ item }) => {
    const isCritical = item.risk_score > 85;
    const color = isCritical ? '#ef4444' : item.risk_score > 60 ? '#f59e0b' : '#10b981';
    return (
      <View style={[styles.threatCard, { borderColor: `${color}30` }]}>
        <View style={styles.threatHeader}>
          <View style={[styles.riskBadge, { backgroundColor: `${color}15` }]}>
            <Ionicons name="warning" size={14} color={color} />
            <Text style={[styles.riskText, { color }]}>Risk {item.risk_score}/100</Text>
          </View>
          <Text style={styles.threatTime}>
            {item.detected_at ? new Date(item.detected_at).toLocaleTimeString() : ''}
          </Text>
        </View>
        <Text style={styles.threatTitle} numberOfLines={2}>{item.alert_reason || item.content || 'Unknown threat'}</Text>
        <View style={styles.threatMeta}>
          <View style={styles.metaChip}>
            <Ionicons name="apps-outline" size={12} color="#64748b" />
            <Text style={styles.metaText}>{item.app_source || item.source || 'Unknown'}</Text>
          </View>
          {item.sender && (
            <View style={styles.metaChip}>
              <Ionicons name="person-outline" size={12} color="#64748b" />
              <Text style={styles.metaText}>{item.sender}</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  const renderAlert = ({ item }) => (
    <View style={styles.alertCard}>
      <View style={{ flex: 1 }}>
        <Text style={styles.alertTitle} numberOfLines={1}>{item.reason || item.message || 'Alert'}</Text>
        <Text style={styles.alertTime}>
          {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
        </Text>
      </View>
      {!item.is_acknowledged && (
        <TouchableOpacity
          style={styles.ackButton}
          onPress={() => ackMutation.mutate(item.id)}
          disabled={ackMutation.isPending}
        >
          <Text style={styles.ackText}>Ack</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <LinearGradient colors={['#020617', '#0f172a']} style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetchThreats} tintColor="#3b82f6" />
        }
        contentContainerStyle={styles.scroll}
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>
              Hello, {user?.name?.split(' ')[0] || 'Agent'} 👋
            </Text>
            <View style={styles.statusPill}>
              <View style={styles.statusDot} />
              <Text style={styles.statusText}>System Monitoring Active</Text>
            </View>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
            <Ionicons name="log-out-outline" size={22} color="#64748b" />
          </TouchableOpacity>
        </View>

        {/* Stats Row */}
        <Text style={styles.sectionLabel}>OVERVIEW</Text>
        {statsLoading ? (
          <ActivityIndicator color="#3b82f6" style={{ marginBottom: 20 }} />
        ) : (
          <View style={styles.statsRow}>
            {renderStatCard('Total Threats', stats?.total_threats, 'skull-outline', '#ef4444')}
            {renderStatCard('Alerts', stats?.total_alerts, 'notifications', '#f59e0b')}
            {renderStatCard('Unread', unackCount, 'alert-circle', '#8b5cf6')}
            {renderStatCard('Targets', stats?.total_targets, 'people-outline', '#3b82f6')}
          </View>
        )}

        {/* Pending Alerts */}
        {alerts.filter(a => !a.is_acknowledged).length > 0 && (
          <>
            <View style={styles.sectionRow}>
              <Text style={styles.sectionLabel}>PENDING ALERTS</Text>
              {unackCount > 0 && (
                <TouchableOpacity onPress={() => ackAllMutation.mutate()} disabled={ackAllMutation.isPending}>
                  <Text style={styles.ackAllText}>Ack All ({unackCount})</Text>
                </TouchableOpacity>
              )}
            </View>
            <FlatList
              data={alerts.filter(a => !a.is_acknowledged).slice(0, 5)}
              keyExtractor={item => item.id?.toString()}
              renderItem={renderAlert}
              scrollEnabled={false}
            />
          </>
        )}

        {/* Recent Threats */}
        <Text style={styles.sectionLabel}>RECENT THREATS</Text>
        {threatsLoading ? (
          <ActivityIndicator color="#3b82f6" />
        ) : threats.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="checkmark-done-circle-outline" size={60} color="#1e293b" />
            <Text style={styles.emptyText}>No threats detected yet</Text>
            <Text style={styles.emptySubtext}>Your device is being actively monitored.</Text>
          </View>
        ) : (
          <FlatList
            data={threats}
            keyExtractor={item => item.id?.toString()}
            renderItem={renderThreat}
            scrollEnabled={false}
          />
        )}
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { paddingHorizontal: 20, paddingTop: 60, paddingBottom: 40 },
  header: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'flex-start', marginBottom: 28,
  },
  greeting: { fontSize: 26, fontWeight: '900', color: '#f8fafc' },
  statusPill: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(16,185,129,0.1)',
    borderRadius: 20, paddingHorizontal: 12, paddingVertical: 6,
    marginTop: 8, alignSelf: 'flex-start',
    borderWidth: 1, borderColor: 'rgba(16,185,129,0.2)',
  },
  statusDot: {
    width: 8, height: 8, borderRadius: 4,
    backgroundColor: '#10b981', marginRight: 6,
  },
  statusText: { color: '#10b981', fontSize: 12, fontWeight: '700' },
  logoutBtn: { padding: 10, backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 50 },
  sectionLabel: {
    fontSize: 11, fontWeight: '800', color: '#475569',
    letterSpacing: 1.5, marginBottom: 12, textTransform: 'uppercase',
  },
  sectionRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  ackAllText: { color: '#3b82f6', fontSize: 13, fontWeight: '700' },
  statsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 28 },
  statCard: {
    flex: 1, minWidth: '44%',
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 16, padding: 16, alignItems: 'flex-start',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)',
  },
  statIconBox: { width: 42, height: 42, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginBottom: 10 },
  statValue: { fontSize: 26, fontWeight: '900', color: '#f8fafc' },
  statLabel: { fontSize: 12, color: '#64748b', marginTop: 4, fontWeight: '600' },
  threatCard: {
    backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: 14,
    padding: 16, marginBottom: 12,
    borderWidth: 1,
  },
  threatHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  riskBadge: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  riskText: { fontSize: 12, fontWeight: '800', marginLeft: 5 },
  threatTime: { color: '#475569', fontSize: 12 },
  threatTitle: { color: '#e2e8f0', fontSize: 14, fontWeight: '600', marginBottom: 10, lineHeight: 20 },
  threatMeta: { flexDirection: 'row', gap: 8 },
  metaChip: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.05)',
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8,
  },
  metaText: { color: '#94a3b8', fontSize: 11, marginLeft: 5, fontWeight: '500' },
  alertCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: 'rgba(245,158,11,0.05)',
    borderRadius: 12, padding: 14, marginBottom: 10,
    borderWidth: 1, borderColor: 'rgba(245,158,11,0.2)',
  },
  alertTitle: { color: '#f8fafc', fontSize: 14, fontWeight: '600' },
  alertTime: { color: '#64748b', fontSize: 11, marginTop: 3 },
  ackButton: {
    backgroundColor: '#3b82f6', borderRadius: 20,
    paddingHorizontal: 14, paddingVertical: 7, marginLeft: 12,
  },
  ackText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  emptyState: { alignItems: 'center', paddingVertical: 40 },
  emptyText: { color: '#94a3b8', fontSize: 17, fontWeight: '700', marginTop: 14 },
  emptySubtext: { color: '#475569', fontSize: 13, marginTop: 6 },
});
