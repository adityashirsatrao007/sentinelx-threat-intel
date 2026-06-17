import httpx
import sys

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "demo@sentinelx.com"
PASSWORD = "SecurePassword123!"

def send_custom_attack(message):
    try:
        # 1. Login to get auth token
        resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        resp.raise_for_status()
        token = resp.json()["access_token"]
        
        # 2. Send the custom attack payload
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "sender": "hacker@unknown.com",
            "message": message,
            "force_risk_score": 9.5  # Bypassing ML for demonstration purposes
        }
        
        print(f"📡 Sending custom attack: '{message}'")
        attack_resp = httpx.post(f"{BASE_URL}/analyze/sms", json=payload, headers=headers)
        
        if attack_resp.status_code == 200:
            result = attack_resp.json()
            print("✅ Threat Logged Successfully!")
            print(f"   Risk Score: {result['risk_score']}/100")
            print(f"   Classification: {result['classification_label'].upper()}")
            print("\n📱 Check your phone screen now!")
        else:
            print(f"⚠️ Failed to send attack: {attack_resp.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 manual_attack.py 'Your malicious message here'")
        sys.exit(1)
    
    send_custom_attack(sys.argv[1])
