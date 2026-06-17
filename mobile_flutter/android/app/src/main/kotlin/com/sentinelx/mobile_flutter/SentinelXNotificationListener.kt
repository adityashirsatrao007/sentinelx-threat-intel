package com.sentinelx.mobile_flutter

import android.content.Intent
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log

/**
 * SentinelX Notification Listener
 * Captures notifications from WhatsApp, Telegram, banking apps, etc.
 * and forwards them to Flutter via a broadcast.
 */
class SentinelXNotificationListener : NotificationListenerService() {

    companion object {
        const val TAG = "SentinelXNotifListener"
        const val ACTION_NOTIFICATION = "com.sentinelx.NOTIFICATION_RECEIVED"

        // Apps we want to monitor
        val MONITORED_PACKAGES = mapOf(
            "com.whatsapp" to "WhatsApp",
            "com.whatsapp.w4b" to "WhatsApp Business",
            "org.telegram.messenger" to "Telegram",
            "org.thunderdog.chalern" to "Telegram X",
            "com.viber.voip" to "Viber",
            "com.facebook.orca" to "Messenger",
            "com.instagram.android" to "Instagram",
            "com.google.android.gm" to "Gmail",
            // Indian Banking Apps
            "com.sbi.SBIFreedomPlus" to "SBI YONO",
            "com.csam.icici.bank.imobile" to "ICICI iMobile",
            "com.axis.mobile" to "Axis Mobile",
            "com.msf.kbank.mobile" to "Kotak",
            "net.one97.paytm" to "Paytm",
            "com.phonepe.app" to "PhonePe",
            "com.google.android.apps.nbu.paisa.user" to "GPay",
            "in.amazon.mShop.android.shopping" to "Amazon",
            "com.flipkart.android" to "Flipkart",
            // Global Banking
            "com.chase.sig.android" to "Chase",
            "com.wf.wellsfargomobile" to "Wells Fargo",
            "com.infonow.bofa" to "Bank of America",
            "com.paypal.android.p2pmobile" to "PayPal",
        )
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn ?: return

        val packageName = sbn.packageName ?: return
        val appName = MONITORED_PACKAGES[packageName] ?: return

        try {
            val extras = sbn.notification?.extras ?: return
            val title = extras.getCharSequence("android.title")?.toString() ?: ""
            val text = extras.getCharSequence("android.text")?.toString() ?: ""
            val bigText = extras.getCharSequence("android.bigText")?.toString() ?: text

            // Skip empty notifications
            if (text.isBlank() && bigText.isBlank()) return

            // Skip ongoing/group summary notifications
            if (sbn.isOngoing) return

            val message = if (bigText.length > text.length) bigText else text

            Log.d(TAG, "Notification from $appName: $title - ${message.take(50)}...")

            // Broadcast to Flutter
            val intent = Intent(ACTION_NOTIFICATION).apply {
                putExtra("app_name", appName)
                putExtra("package_name", packageName)
                putExtra("sender", title)
                putExtra("message", message)
                putExtra("timestamp", System.currentTimeMillis().toString())
                setPackage(this@SentinelXNotificationListener.packageName)
            }
            sendBroadcast(intent)

        } catch (e: Exception) {
            Log.e(TAG, "Error processing notification from $packageName", e)
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        // Not needed for threat detection
    }
}
