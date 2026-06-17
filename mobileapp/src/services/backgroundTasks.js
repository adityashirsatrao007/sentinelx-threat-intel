import * as TaskManager from 'expo-task-manager';
import * as BackgroundFetch from 'expo-background-fetch';
import Constants from 'expo-constants';
import api from './api';

const BACKGROUND_MONITOR_TASK = 'BACKGROUND_MONITOR_TASK';
const IS_EXPO_GO = Constants.appOwnership === 'expo';

// Only call expo-notifications in production builds — it crashes in Expo Go SDK 53+
if (!IS_EXPO_GO) {
  const Notifications = require('expo-notifications');
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: true,
    }),
  });
}

// Define the background task — safe to register even in Expo Go (just won't execute)
TaskManager.defineTask(BACKGROUND_MONITOR_TASK, async () => {
  try {
    console.log('Background task running: Scanning for threats...');

    const mockThreatDetected = Math.random() > 0.8;

    if (mockThreatDetected && !IS_EXPO_GO) {
      const Notifications = require('expo-notifications');
      await Notifications.scheduleNotificationAsync({
        content: {
          title: '⚠️ High Risk Scam Detected',
          body: 'Phishing URL detected in incoming message',
        },
        trigger: null,
      });
    }

    return BackgroundFetch.BackgroundFetchResult.NewData;
  } catch (error) {
    console.error('Background task error:', error);
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

export const registerBackgroundTasks = async () => {
  if (IS_EXPO_GO) {
    console.log('Background tasks skipped in Expo Go.');
    return;
  }
  try {
    await BackgroundFetch.registerTaskAsync(BACKGROUND_MONITOR_TASK, {
      minimumInterval: 15 * 60,
      stopOnTerminate: false,
      startOnBoot: true,
    });
    console.log('Background monitoring registered successfully.');
  } catch (err) {
    console.log('Background task registration skipped:', err.message);
  }
};
