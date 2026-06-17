import httpx

BASE_URL = "http://localhost:8000/api/v1"
email = "demo@sentinelx.com"
password = "SecurePassword123!"

def create_user():
    print("Attempting to create demo user...")
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Check health first
        try:
            resp = client.get("http://localhost:8000/health")
            if resp.status_code != 200:
                print(f"Backend not healthy. Status: {resp.status_code}")
                return
        except Exception as e:
            print(f"Connection failed: {e}")
            return
            
        resp = client.post("/auth/register", json={
            "name": "Demo Admin",
            "email": email,
            "password": password,
            "role": "sysadmin",
            "organization_name": "Demo Org"
        })
        
        if resp.status_code in [201, 409]: # 409 is already exists
            print("\n✅ Demo User Ready!")
            print(f"Email (ID): {email}")
            print(f"Password:   {password}")
        else:
            print(f"Failed to create user: {resp.text}")

if __name__ == "__main__":
    create_user()
