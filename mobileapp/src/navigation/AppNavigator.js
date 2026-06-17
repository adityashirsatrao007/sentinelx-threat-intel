import React, { useContext } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ActivityIndicator, View } from 'react-native';
import { AuthContext } from '../context/AuthContext';

import LoginScreen from '../screens/LoginScreen';
import OnboardingScreen from '../screens/OnboardingScreen';
import HomeScreen from '../screens/HomeScreen';

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  const { isLoading, userToken, isOnboarded } = useContext(AuthContext);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0f172a' }}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#0f172a' } }}>
        {userToken == null ? (
          // User is not signed in
          <Stack.Screen name="Login" component={LoginScreen} />
        ) : !isOnboarded ? (
          // User is signed in but hasn't completed onboarding/permissions
          <Stack.Screen name="Onboarding" component={OnboardingScreen} />
        ) : (
          // Fully onboarded user
          <Stack.Screen name="Home" component={HomeScreen} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
