import React, { createContext, useState, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';
import { authAPI } from '../services/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [userToken, setUserToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isOnboarded, setIsOnboarded] = useState(false);

  useEffect(() => {
    const bootstrapAsync = async () => {
      try {
        const token = await SecureStore.getItemAsync('userToken');
        const onboarded = await SecureStore.getItemAsync('isOnboarded');
        if (token) {
          setUserToken(token);
          // Fetch user profile to confirm token is still valid
          try {
            const res = await authAPI.me();
            setUser(res.data);
          } catch {
            // Token expired — clear it
            await SecureStore.deleteItemAsync('userToken');
            setUserToken(null);
          }
        }
        setIsOnboarded(onboarded === 'true');
      } catch (e) {
        console.warn('Bootstrap error:', e);
      } finally {
        setIsLoading(false);
      }
    };
    bootstrapAsync();
  }, []);

  const login = async (token, userData) => {
    try {
      await SecureStore.setItemAsync('userToken', token);
    } catch (e) {
      console.warn('SecureStore failed:', e);
    }
    setUserToken(token);
    setUser(userData);
  };

  const completeOnboarding = async () => {
    try {
      await SecureStore.setItemAsync('isOnboarded', 'true');
    } catch (e) {}
    setIsOnboarded(true);
  };

  const logout = async () => {
    try {
      await SecureStore.deleteItemAsync('userToken');
      await SecureStore.deleteItemAsync('isOnboarded');
    } catch (e) {}
    setUserToken(null);
    setUser(null);
    setIsOnboarded(false);
  };

  return (
    <AuthContext.Provider value={{ isLoading, userToken, user, isOnboarded, login, completeOnboarding, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
