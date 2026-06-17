import pandas as pd
import email
from email.policy import default
import httpx
import time
import random

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "demo@sentinelx.com"
PASSWORD = "SecurePassword123!"

def get_token():
    resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]

def parse_email_message(raw_content):
    msg = email.message_from_string(raw_content, policy=default)
    subject = msg.get('Subject', '(No Subject)')
    sender = msg.get('From', 'unknown@enron.com')
    
    # Simple body extraction
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode(errors='replace')
                break
    else:
        body = msg.get_payload(decode=True).decode(errors='replace')
    
    return sender, subject, body

def seed_enron_data(token, csv_path):
    df = pd.read_csv(csv_path)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Department/Role mapping for realism
    depts = ["Finance", "Legal", "Executive", "Engineering", "Operations", "Marketing"]
    roles = ["Director", "Manager", "Analyst", "Counsel", "Specialist"]
    
    print(f"\n📨 Processing {len(df)} Enron emails for SentinelX...")
    
    for i, row in df.iterrows():
        sender, subject, body = parse_email_message(row['message'])
        
        # Randomly "phishify" some emails to ensure we have threats
        is_phish = random.random() < 0.2
        if is_phish:
            body += "\n\nURGENT: Please verify your account at https://enron-it-portal.net/verify"
            subject = "[Action Required] " + subject
            
        payload = {
            "sender": sender,
            "subject": subject,
            "body": body[:5000], # limit body size
            "target_department": random.choice(depts),
            "target_role": random.choice(roles)
        }
        
        try:
            resp = httpx.post(f"{BASE_URL}/analyze/email", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                r = resp.json()
                status = "🚨 THREAT" if r['threat_detected'] else "✅ SAFE"
                print(f"  {status} | Risk: {r['risk_score']} | From: {sender[:30]}")
            else:
                print(f"  ⚠️  Error {resp.status_code}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            
        # Small delay to avoid hammering
        time.sleep(0.2)

if __name__ == "__main__":
    try:
        token = get_token()
        seed_enron_data(token, "backend/enron_subset.csv")
    except Exception as e:
        print(f"Error: {e}")
