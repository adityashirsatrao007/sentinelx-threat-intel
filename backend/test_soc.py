import httpx
import uuid
import time
from pprint import pprint

BASE_URL = "http://localhost:8000/api/v1"

def print_step(title):
    print(f"\n{'='*50}\n🚀 {title}\n{'='*50}")

def run_tests():
    # Credentials to hand over to the user
    soc_email = f"soc_admin_{uuid.uuid4().hex[:6]}@example.com"
    soc_password = "SecurePassword123!"
    org_name = f"Global Security SOC {uuid.uuid4().hex[:6]}"
    
    user_email = f"operator_{uuid.uuid4().hex[:6]}@example.com"
    user_password = "UserPassword123!"

    with httpx.Client(base_url=BASE_URL, timeout=120.0) as client:
        
        # ─── 1. Register SOC Admin ────────────────────────────────────────────────
        print_step("Registering SOC Admin & Organization")
        resp = client.post("/auth/register", json={
            "name": "Head of Security",
            "email": soc_email,
            "password": soc_password,
            "role": "soc",
            "organization_name": org_name
        })
        
        # If already exists from previous runs, we just log in
        if resp.status_code == 409:
            print("SOC Admin already exists, skipping registration.")
        else:
            assert resp.status_code == 201, f"Failed: {resp.text}"
            print(f"✅ SOC Admin registered: {soc_email} under org '{org_name}'")

        # Login as SOC Admin
        resp = client.post("/auth/login", json={"email": soc_email, "password": soc_password})
        assert resp.status_code == 200, f"Failed: {resp.text}"
        soc_token = resp.json()["access_token"]
        soc_headers = {"Authorization": f"Bearer {soc_token}"}
        print("✅ Logged in as SOC Admin.")

        # ─── 2. Invite a Test User to the Organization ────────────────────────────
        print_step("Inviting Test User")
        resp = client.post("/auth/invite", headers=soc_headers, json={
            "name": "Test Operator",
            "email": user_email,
            "password": user_password,
            "role": "operator"
        })
        assert resp.status_code == 201, f"Failed: {resp.text}"
        print(f"✅ User invited successfully: {user_email}")

        # ─── 3. Login as Test User & Submit Threat ──────────────────────────────
        print_step("User: Submitting Fake Threat")
        resp = client.post("/auth/login", json={"email": user_email, "password": user_password})
        assert resp.status_code == 200, f"Failed: {resp.text}"
        user_token = resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        resp = client.post("/analyze/email", headers=user_headers, json={
            "sender": "hacker@evil-domain.com",
            "subject": "Wire Transfer Required",
            "body": "Please wire $50,000 to the following offshore account immediately. This is highly urgent."
        })
        assert resp.status_code == 200, f"Failed: {resp.text}"
        print("✅ Threat analyzed and logged by user.")
        
        # ─── 4. Verify SOC Admin Dashboard Aggregation ────────────────────────────
        print_step("SOC Dashboard: Verifying Aggregation")
        resp = client.get("/dashboard/stats", headers=soc_headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        stats = resp.json()
        print("✅ SOC Dashboard Stats Retrieved:")
        pprint(stats)
        
        # Since this is a dedicated test org, it should only see the threats from THIS flow.
        # But if the script runs multiple times, it will aggregate them. We just verify it's >= 1.
        assert stats["total_threats"] >= 1, "Expected at least 1 threat in SOC dashboard."
        print("\n🎉 MULTI-TENANCY TEST PASSED! The SOC Admin successfully sees the user's data. 🎉")

if __name__ == "__main__":
    run_tests()
