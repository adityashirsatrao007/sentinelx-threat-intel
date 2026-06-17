import httpx
import time
import random
import sys

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "demo@sentinelx.com"
PASSWORD = "SecurePassword123!"

ATTACK_TEMPLATES = [
    {
        "sender": "it-security@enron-internal.com",
        "subject": "[URGENT] Security Patch Required for Outlook",
        "body": "Dear Employee, A critical vulnerability has been found in the desktop version of Outlook. To prevent unauthorized access to your mailbox, please install the security patch immediately: http://enron-patch-update.net/download. Regards, IT Security Team.",
        "dept": "Operations",
        "role": "Manager"
    },
    {
        "sender": "payroll@enron-finance.net",
        "subject": "Delayed Salary Payment - Action Needed",
        "body": "Your salary payment for this month is currently on hold due to a mismatch in banking details. Please verify your account information at http://enron-payroll-verify.io to ensure timely payment.",
        "dept": "Finance",
        "role": "Analyst"
    },
    {
        "sender": "ken.lay@enron.com",
        "subject": "Confidential Request",
        "body": "I'm in a meeting and need a quick favor. Please purchase 10 Apple Gift cards ($500 each) and send the codes to my personal email. This is urgent for a client gift. I will reimburse you by the end of the day.",
        "dept": "Executive",
        "role": "Director"
    },
    {
        "sender": "noreply@microsoft-security.com",
        "subject": "Suspicious login from Lagos, Nigeria",
        "body": "We detected a login to your account from an unrecognized device. If this wasn't you, please secure your account: http://microsoft-auth-verify.com/secure",
        "dept": "Engineering",
        "role": "Specialist"
    },
    {
        "sender": "hr-portal@enron-careers.org",
        "subject": "Updated Employee Handbook - Signature Required",
        "body": "The employee handbook has been updated. All staff are required to review and sign the new policy agreement by Friday. Login here: http://enron-hr-policy.net/login",
        "dept": "Marketing",
        "role": "Coordinator"
    }
]

def get_token():
    try:
        resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=10)
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        print(f"❌ Could not login: {e}")
        sys.exit(1)

def run_simulator():
    print("🚀 Starting SentinelX Real-time Attack Simulator...")
    print("Press Ctrl+C to stop.\n")
    
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    while True:
        template = random.choice(ATTACK_TEMPLATES)
        
        # Add a bit of randomness to the sender/subject to make it look unique
        payload = {
            "sender": template["sender"],
            "subject": f"{template['subject']} #{random.randint(100, 999)}",
            "body": template["body"],
            "target_department": template["dept"],
            "target_role": template["role"]
        }
        
        try:
            print(f"📡 Sending simulated attack from {payload['sender']}...")
            resp = httpx.post(f"{BASE_URL}/analyze/email", json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ Threat Logged | Risk: {result['risk_score']}/10 | Type: {result['classification_label']}")
            else:
                print(f"⚠️ API Error: {resp.status_code}")
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            
        # Wait between 5 to 12 seconds for the next attack
        wait_time = random.uniform(5, 12)
        print(f"⏳ Next attack in {wait_time:.1f}s...\n")
        time.sleep(wait_time)

if __name__ == "__main__":
    run_simulator()
