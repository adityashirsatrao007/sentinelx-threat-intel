"""
SentinelX Demo Seed Script
Populates the database with realistic threat and alert data via the live API.
"""
import httpx
import time
import random

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "demo@sentinelx.com"
PASSWORD = "SecurePassword123!"

PHISHING_EMAILS = [
    {
        "sender": "security-alert@paypa1-support.xyz",
        "subject": "URGENT: Your PayPal account has been suspended",
        "body": "Dear valued customer, we have detected suspicious activity on your PayPal account. Your account has been temporarily suspended. Click here immediately to verify your identity: http://bit.ly/paypal-verify-now. Failure to verify within 24 hours will result in permanent account closure.",
    },
    {
        "sender": "noreply@amazon-security-center.net",
        "subject": "Action Required: Unauthorized Access Detected",
        "body": "We have detected an unauthorized sign-in attempt on your Amazon account from a new device in Russia. If this was not you, click here to secure your account: https://amaz0n-secure.ru/verify. Your account will be locked if you do not respond.",
    },
    {
        "sender": "admin@microsoft-account-alert.com",
        "subject": "Your Microsoft 365 subscription is expiring",
        "body": "Your Microsoft 365 license expires in 24 hours. To avoid losing access to your files and emails, please update your payment information immediately. Visit: http://tinyurl.com/ms365-renew. Provide your credit card details to continue service.",
    },
    {
        "sender": "hr.department@your-company-payroll.tk",
        "subject": "Immediate Payroll Update Required",
        "body": "Dear Employee, due to a system migration, all employees must re-verify their direct deposit banking information before Friday. Please click the link below and enter your bank account number and routing number to ensure you receive your paycheck: http://payroll-update.tk/form",
    },
    {
        "sender": "ceo.johnson@companynamecorp.online",
        "subject": "Confidential Wire Transfer Request - Urgent",
        "body": "I need you to process an urgent wire transfer of $47,500 to our new vendor account. This is time-sensitive for a deal closing today. Account: 8827634910, Routing: 021000021. Do not discuss this with anyone else. I'll explain everything later. - CEO",
    },
    {
        "sender": "irs-refund@gov-tax-refund.us",
        "subject": "IRS Tax Refund Notification - $1,847.00",
        "body": "Congratulations! The IRS has calculated your tax refund amount of $1,847.00. To receive your refund, you must provide your Social Security Number, bank account details, and credit card information for verification. Respond within 48 hours: http://irs-gov-refund.us/claim",
    },
    {
        "sender": "security@netfl1x-billing.com",
        "subject": "Netflix Payment Failed - Account On Hold",
        "body": "Your Netflix payment method was declined. Your account is currently on hold. To continue watching, please update your billing information immediately: http://netfl1x-billing.com/update-payment. Enter your credit card number, expiry, and CVV.",
    },
    {
        "sender": "phishing@crypto-wallet-recover.io",
        "subject": "Your Coinbase Wallet Requires Verification",
        "body": "Unusual activity detected on your Coinbase account. Your cryptocurrency wallet has been flagged and will be frozen in 2 hours unless you verify ownership. Provide your 12-word seed phrase here: http://coinbase-verify.io/wallet-check to prevent permanent loss of funds.",
    },
]

SCAM_SMS = [
    {
        "sender": "+18005551234",
        "message": "CONGRATULATIONS! You've been selected to receive a FREE iPhone 15 Pro! Claim your prize before it expires: http://free-iphone-winner.com/claim?id=89234. Limited time offer!",
    },
    {
        "sender": "+12125559876",
        "message": "ALERT: Your bank account has been compromised. Call 1-800-555-BANK immediately or visit http://secure-bank-verify.net to secure your funds NOW.",
    },
    {
        "sender": "+17145558765",
        "message": "Your package could not be delivered. Update your delivery address: http://usps-redelivery.com/track?pkg=US9283847. Reply STOP to opt out.",
    },
    {
        "sender": "+13105554321",
        "message": "Crypto investment opportunity! Earn $5000/week guaranteed with our AI trading bot. Initial investment of $500 required. DM us or visit http://crypto-gains-ai.com",
    },
    {
        "sender": "+16505552468",
        "message": "Your Social Security Number has been suspended due to suspicious activity. Call 1-888-555-9999 immediately to restore your SSN before legal action begins.",
    },
]

def get_token():
    resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]

def seed_threats(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    created = 0

    print("\n📧 Seeding phishing email threats...")
    for sample in PHISHING_EMAILS:
        try:
            resp = httpx.post(f"{BASE_URL}/analyze/email", headers=headers, json=sample, timeout=30)
            if resp.status_code == 200:
                r = resp.json()
                print(f"  ✅ Email threat | Risk: {r['risk_score']} | Level: {r['threat_level']} | {sample['subject'][:50]}")
                created += 1
            else:
                print(f"  ⚠️  {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        time.sleep(0.3)

    print("\n📱 Seeding SMS scam threats...")
    for sample in SCAM_SMS:
        try:
            resp = httpx.post(f"{BASE_URL}/analyze/sms", headers=headers, json=sample, timeout=30)
            if resp.status_code == 200:
                r = resp.json()
                print(f"  ✅ SMS threat | Risk: {r['risk_score']} | Level: {r['threat_level']} | {sample['message'][:50]}")
                created += 1
            else:
                print(f"  ⚠️  {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        time.sleep(0.3)

    return created

def verify_dashboard(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE_URL}/dashboard/stats", headers=headers, timeout=15)
    stats = resp.json()
    print(f"\n📊 Dashboard Stats After Seeding:")
    print(f"  Total Threats:      {stats['total_threats']}")
    print(f"  Phishing Attempts:  {stats['phishing_attempts']}")
    print(f"  Critical Alerts:    {stats['critical_alerts']}")
    print(f"  Avg Risk Score:     {stats['avg_risk_score']}")
    print(f"  Threats Today:      {stats['threats_today']}")

if __name__ == "__main__":
    print("🚀 SentinelX Demo Data Seeder")
    print("=" * 40)
    
    print(f"\n🔐 Logging in as {EMAIL}...")
    try:
        token = get_token()
        print("✅ Login successful.")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        exit(1)

    n = seed_threats(token)
    print(f"\n✅ Seeding complete! Created {n} threats.")
    
    verify_dashboard(token)
    print("\n🎉 Done! Refresh the SentinelX dashboard to see the data.")
