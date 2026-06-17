import React, { useState, useContext, useRef, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Animated, Easing, Alert, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../context/AuthContext';
import { authAPI } from '../services/api';
import { useMutation } from '@tanstack/react-query';

export default function LoginScreen() {
  const { login } = useContext(AuthContext);
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(40)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 900, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 700, easing: Easing.out(Easing.exp), useNativeDriver: true }),
    ]).start();
  }, []);

  const loginMutation = useMutation({
    mutationFn: () => authAPI.login(email.trim(), password),
    onSuccess: async (res) => {
      const token = res.data.access_token;
      // Fetch user profile after login
      const userRes = await authAPI.me();
      login(token, userRes.data);
    },
    onError: (err) => {
      console.error('[LOGIN ERROR]', err.message, err.response?.status, err.response?.data);
      const msg = err.response?.data?.detail || err.message || 'Login failed. Check your credentials.';
      Alert.alert('Login Failed', msg);
    },
  });

  const signupMutation = useMutation({
    mutationFn: () => authAPI.register(name.trim(), email.trim(), password),
    onSuccess: async () => {
      // Auto-login after registration
      const res = await authAPI.login(email.trim(), password);
      const token = res.data.access_token;
      const userRes = await authAPI.me();
      login(token, userRes.data);
    },
    onError: (err) => {
      console.error('[SIGNUP ERROR]', err.message, err.response?.status, err.response?.data);
      const msg = err.response?.data?.detail || err.message || 'Registration failed. Email may already exist.';
      Alert.alert('Sign Up Failed', msg);
    },
  });

  const isPending = loginMutation.isPending || signupMutation.isPending;

  const handleSubmit = () => {
    if (!email || !password) return Alert.alert('Missing Fields', 'Email and password are required.');
    if (mode === 'signup' && !name) return Alert.alert('Missing Fields', 'Please enter your name.');
    if (mode === 'login') loginMutation.mutate();
    else signupMutation.mutate();
  };

  return (
    <LinearGradient colors={['#0f172a', '#020617']} style={styles.container}>
      <View style={styles.glowCircle1} />
      <View style={styles.glowCircle2} />

      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} keyboardShouldPersistTaps="handled">
          <Animated.View style={[styles.content, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
            {/* Brand */}
            <View style={styles.brand}>
              <Ionicons name="shield-checkmark" size={64} color="#3b82f6" />
              <Text style={styles.logoText}>SentinelX</Text>
              <Text style={styles.tagline}>Threat intelligence for everyone.</Text>
            </View>

            {/* Tabs */}
            <View style={styles.tabs}>
              <TouchableOpacity style={[styles.tab, mode === 'login' && styles.tabActive]} onPress={() => setMode('login')}>
                <Text style={[styles.tabText, mode === 'login' && styles.tabTextActive]}>Sign In</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.tab, mode === 'signup' && styles.tabActive]} onPress={() => setMode('signup')}>
                <Text style={[styles.tabText, mode === 'signup' && styles.tabTextActive]}>Sign Up</Text>
              </TouchableOpacity>
            </View>

            {/* Form */}
            <View style={styles.form}>
              {mode === 'signup' && (
                <View style={styles.inputWrapper}>
                  <Ionicons name="person-outline" size={18} color="#64748b" style={styles.inputIcon} />
                  <TextInput
                    style={styles.input}
                    placeholder="Full Name"
                    placeholderTextColor="#475569"
                    value={name}
                    onChangeText={setName}
                    autoCapitalize="words"
                  />
                </View>
              )}
              <View style={styles.inputWrapper}>
                <Ionicons name="mail-outline" size={18} color="#64748b" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Email Address"
                  placeholderTextColor="#475569"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>
              <View style={styles.inputWrapper}>
                <Ionicons name="lock-closed-outline" size={18} color="#64748b" style={styles.inputIcon} />
                <TextInput
                  style={[styles.input, { flex: 1 }]}
                  placeholder="Password"
                  placeholderTextColor="#475569"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPass}
                />
                <TouchableOpacity onPress={() => setShowPass(!showPass)} style={{ paddingRight: 16 }}>
                  <Ionicons name={showPass ? 'eye-off-outline' : 'eye-outline'} size={18} color="#64748b" />
                </TouchableOpacity>
              </View>

              <TouchableOpacity
                style={[styles.submitButton, isPending && styles.submitDisabled]}
                onPress={handleSubmit}
                disabled={isPending}
                activeOpacity={0.85}
              >
                <LinearGradient colors={['#3b82f6', '#1d4ed8']} style={styles.submitGradient}>
                  {isPending
                    ? <ActivityIndicator color="#fff" />
                    : <Text style={styles.submitText}>{mode === 'login' ? 'Sign In' : 'Create Account'}</Text>
                  }
                </LinearGradient>
              </TouchableOpacity>
            </View>

            <Text style={styles.footerText}>🔒 Secured with end-to-end encryption</Text>
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  glowCircle1: {
    position: 'absolute', top: -120, left: -80,
    width: 300, height: 300, borderRadius: 150,
    backgroundColor: '#3b82f6', opacity: 0.12,
  },
  glowCircle2: {
    position: 'absolute', bottom: -100, right: -80,
    width: 350, height: 350, borderRadius: 175,
    backgroundColor: '#8b5cf6', opacity: 0.1,
  },
  content: { padding: 28 },
  brand: { alignItems: 'center', marginBottom: 36 },
  logoText: { fontSize: 44, fontWeight: '900', color: '#f8fafc', letterSpacing: 1.5, marginTop: 12 },
  tagline: { fontSize: 14, color: '#94a3b8', marginTop: 6 },
  tabs: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 14,
    padding: 4,
    marginBottom: 28,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center', borderRadius: 10 },
  tabActive: { backgroundColor: '#1e40af' },
  tabText: { color: '#64748b', fontWeight: '600', fontSize: 15 },
  tabTextActive: { color: '#f8fafc' },
  form: { gap: 14 },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  inputIcon: { paddingLeft: 16, paddingRight: 8 },
  input: {
    flex: 1,
    paddingVertical: 15,
    paddingRight: 16,
    color: '#f8fafc',
    fontSize: 15,
  },
  submitButton: { borderRadius: 100, marginTop: 8, overflow: 'hidden' },
  submitDisabled: { opacity: 0.6 },
  submitGradient: {
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitText: { color: '#fff', fontSize: 17, fontWeight: '800' },
  footerText: { textAlign: 'center', color: '#475569', fontSize: 12, marginTop: 28 },
});
