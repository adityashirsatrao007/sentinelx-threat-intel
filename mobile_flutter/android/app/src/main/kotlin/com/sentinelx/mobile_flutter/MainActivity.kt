package com.sentinelx.mobile_flutter

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.provider.Telephony
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val SMS_CHANNEL = "com.sentinelx/sms"
    private val NOTIF_CHANNEL = "com.sentinelx/notifications"
    private var smsReceiver: BroadcastReceiver? = null
    private var notifReceiver: BroadcastReceiver? = null
    private var smsMethodChannel: MethodChannel? = null
    private var notifMethodChannel: MethodChannel? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // ─── SMS MethodChannel ───────────────────────────────────────────────
        smsMethodChannel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, SMS_CHANNEL)

        smsReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (intent?.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
                    val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
                    for (msg in messages) {
                        val smsData = mapOf(
                            "sender" to (msg.displayOriginatingAddress ?: "Unknown"),
                            "message" to (msg.displayMessageBody ?: ""),
                            "timestamp" to msg.timestampMillis.toString()
                        )
                        smsMethodChannel?.invokeMethod("onSmsReceived", smsData)
                    }
                }
            }
        }

        val smsFilter = IntentFilter(Telephony.Sms.Intents.SMS_RECEIVED_ACTION)
        smsFilter.priority = IntentFilter.SYSTEM_HIGH_PRIORITY
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(smsReceiver, smsFilter, RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(smsReceiver, smsFilter)
        }

        // ─── Notifications MethodChannel ─────────────────────────────────────
        notifMethodChannel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, NOTIF_CHANNEL)

        notifReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                if (intent?.action == SentinelXNotificationListener.ACTION_NOTIFICATION) {
                    val notifData = mapOf(
                        "app_name" to (intent.getStringExtra("app_name") ?: ""),
                        "package_name" to (intent.getStringExtra("package_name") ?: ""),
                        "sender" to (intent.getStringExtra("sender") ?: ""),
                        "message" to (intent.getStringExtra("message") ?: ""),
                        "timestamp" to (intent.getStringExtra("timestamp") ?: "")
                    )
                    notifMethodChannel?.invokeMethod("onNotificationReceived", notifData)
                }
            }
        }

        val notifFilter = IntentFilter(SentinelXNotificationListener.ACTION_NOTIFICATION)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(notifReceiver, notifFilter, RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(notifReceiver, notifFilter)
        }

        // ─── Method call handler for Flutter → Native ────────────────────────
        notifMethodChannel?.setMethodCallHandler { call, result ->
            when (call.method) {
                "isNotificationAccessGranted" -> {
                    val enabled = android.provider.Settings.Secure.getString(
                        contentResolver,
                        "enabled_notification_listeners"
                    )
                    result.success(enabled?.contains(packageName) == true)
                }
                "openNotificationSettings" -> {
                    startActivity(Intent("android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS"))
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }
    }

    override fun onDestroy() {
        smsReceiver?.let { unregisterReceiver(it) }
        notifReceiver?.let { unregisterReceiver(it) }
        super.onDestroy()
    }
}
