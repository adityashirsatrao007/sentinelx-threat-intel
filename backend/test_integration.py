import httpx
import uuid
import time
from pprint import pprint

BASE_URL = "http://localhost:8000/api/v1"

def print_step(title):
    print(f"\n{'='*50}\n🚀 {title}\n{'='*50}")

def run_tests():
    with httpx.Client(base_url=BASE_URL, timeout=120.0) as client:
        
        # ─── 1. Health Check (Root isn't /api/v1, so we do absolute)
        print_step("Checking Health")
        resp = httpx.get("http://localhost:8000/health")
        assert resp.status_code == 200
        print("✅ Health check passed!")
        print(resp.json())

        # ─── 2. Register a new user
        print_step("Registering User")
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_{unique_id}@example.com"
        password = "SecurePassword123!"
        
        resp = client.post("/auth/register", json={
            "name": "Integration Tester",
            "email": email,
            "password": password,
            "role": "admin"
        })
        assert resp.status_code == 201, f"Failed: {resp.text}"
        print(f"✅ User registered successfully: {email}")

        # ─── 3. Login to get JWT Token
        print_step("Logging In")
        resp = client.post("/auth/login", json={
            "email": email,
            "password": password
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully. Token received.")

        # ─── 4. Analyze a Phishing Email
        print_step("Analyzing Phishing Email")
        resp = client.post("/analyze/email", headers=headers, json={
            "sender": "security@paypa1-alert.xyz",
            "subject": "URGENT: Your account has been suspended",
            "body": "Click here immediately to verify your account and avoid permanent suspension. Provide your password. https://bit.ly/fake-link"
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        email_result = resp.json()
        print("✅ Email analyzed successfully!")
        print(f"Threat Detected: {email_result['threat_detected']}")
        print(f"Risk Score: {email_result['risk_score']} ({email_result['threat_level']})")
        print("Reasons:")
        for r in email_result["reasons"]:
            print(f"  - {r}")

        # ─── 5. Analyze an SMS Scam
        print_step("Analyzing SMS Scam")
        resp = client.post("/analyze/sms", headers=headers, json={
            "sender": "+18005559999",
            "message": "Congratulations! You've won a free iPhone. Claim your prize now: http://tinyurl.com/claim-prize"
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        sms_result = resp.json()
        print("✅ SMS analyzed successfully!")
        print(f"Risk Score: {sms_result['risk_score']} ({sms_result['threat_level']})")

        # ─── 6. Fetch Dashboard Stats
        print_step("Fetching Dashboard Stats")
        resp = client.get("/dashboard/stats", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        stats = resp.json()
        print("✅ Dashboard stats retrieved:")
        pprint(stats)

        # ─── 7. Fetch Alerts
        print_step("Fetching Generated Alerts")
        resp = client.get("/alerts?unacknowledged_only=true", headers=headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        alerts = resp.json()["alerts"]
        print(f"✅ Found {len(alerts)} unacknowledged alerts.")
        
        if alerts:
            # ─── 8. Acknowledge an Alert
            alert_id = alerts[0]["id"]
            print_step(f"Acknowledging Alert {alert_id}")
            resp = client.post(f"/alerts/{alert_id}/acknowledge", headers=headers)
            assert resp.status_code == 200, f"Failed: {resp.text}"
            print("✅ Alert acknowledged successfully!")
        
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! The backend is working perfectly. 🎉")

if __name__ == "__main__":
    run_tests()
