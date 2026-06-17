"""
SentinelX — Full API Health Check
Tests every registered route against the live local backend.
"""
import httpx

BASE = "http://localhost:8000"
API  = f"{BASE}/api/v1"
EMAIL    = "demo@sentinelx.com"
PASSWORD = "SecurePassword123!"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = []
failed = []

def check(label, status, expected=(200,201,202), body=None):
    ok = status in expected
    symbol = f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"
    note   = f"{YELLOW}[{status}]{RESET}"
    print(f"  {symbol} {note} {label}")
    if ok:
        passed.append(label)
    else:
        detail = body[:120] if body else ""
        print(f"     {RED}↳ {detail}{RESET}")
        failed.append(label)
    return ok

def section(title):
    print(f"\n{BOLD}{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*55}{RESET}")

# ─── Auth ─────────────────────────────────────────────────────────────────────
section("1. HEALTH & AUTH")
with httpx.Client(base_url=BASE, timeout=15) as c:
    r = c.get("/health")
    check("GET /health", r.status_code, (200,))

    r = c.post(f"{API}/auth/register", json={
        "name": "Test Runner", "email": "testrunner_debug@sentinelx.com",
        "password": "TestPass123!", "role": "user"
    })
    check("POST /auth/register (new user)", r.status_code, (201, 409))

    r = c.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    login_ok = check("POST /auth/login", r.status_code, (200,), r.text)
    if not login_ok:
        print(f"\n{RED}Cannot continue without auth token. Check credentials.{RESET}")
        exit(1)
    
    TOKEN = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {TOKEN}"}

    r = c.get(f"{API}/auth/me", headers=headers)
    check("GET /auth/me", r.status_code, (200,))
    if r.status_code == 200:
        user = r.json()
        print(f"     {CYAN}↳ Logged in as: {user['name']} | role: {user['role']}{RESET}")

    r = c.get(f"{API}/auth/users", headers=headers)
    check("GET /auth/users", r.status_code, (200,))

# ─── Dashboard ────────────────────────────────────────────────────────────────
section("2. DASHBOARD")
with httpx.Client(base_url=BASE, timeout=15) as c:
    r = c.get(f"{API}/dashboard/stats", headers=headers)
    check("GET /dashboard/stats", r.status_code, (200,))
    if r.status_code == 200:
        s = r.json()
        print(f"     {CYAN}↳ Threats: {s.get('total_threats')} | Alerts: {s.get('total_alerts')} | Avg Risk: {s.get('avg_risk_score')}{RESET}")

    r = c.get(f"{API}/dashboard/threats?skip=0&limit=10", headers=headers)
    check("GET /dashboard/threats", r.status_code, (200,))
    if r.status_code == 200:
        data = r.json()
        count = len(data.get('threats', []))
        print(f"     {CYAN}↳ Returned {count} threats{RESET}")

    r = c.get(f"{API}/dashboard/trends?days=7", headers=headers)
    check("GET /dashboard/trends", r.status_code, (200,))

    r = c.get(f"{API}/dashboard/targets", headers=headers)
    check("GET /dashboard/targets", r.status_code, (200,))

# ─── Alerts ───────────────────────────────────────────────────────────────────
section("3. ALERTS")
with httpx.Client(base_url=BASE, timeout=15) as c:
    r = c.get(f"{API}/alerts", headers=headers)
    check("GET /alerts", r.status_code, (200,))

    r = c.get(f"{API}/alerts?unacknowledged_only=true", headers=headers)
    check("GET /alerts?unacknowledged_only=true", r.status_code, (200,))
    if r.status_code == 200:
        alerts = r.json().get("alerts", [])
        print(f"     {CYAN}↳ {len(alerts)} unacknowledged alerts{RESET}")
        alert_id = alerts[0]["id"] if alerts else None
    else:
        alert_id = None

    if alert_id:
        r = c.post(f"{API}/alerts/{alert_id}/acknowledge", headers=headers)
        check("POST /alerts/{id}/acknowledge", r.status_code, (200,))

    r = c.post(f"{API}/alerts/acknowledge-all", headers=headers)
    check("POST /alerts/acknowledge-all", r.status_code, (200,))

# ─── Analyze ──────────────────────────────────────────────────────────────────
section("4. ANALYZE")
with httpx.Client(base_url=BASE, timeout=30) as c:
    r = c.post(f"{API}/analyze/sms", headers=headers, json={
        "sender": "+1800555TEST",
        "message": "URGENT: Click http://phish.site to verify your bank account now!"
    })
    check("POST /analyze/sms", r.status_code, (200,), r.text)
    if r.status_code == 200:
        d = r.json()
        print(f"     {CYAN}↳ Risk: {d.get('risk_score')} | Level: {d.get('threat_level')}{RESET}")

    r = c.post(f"{API}/analyze/email", headers=headers, json={
        "sender": "no-reply@fake-paypal.xyz",
        "subject": "Verify your account immediately",
        "body": "Your account will be suspended. Click here: http://evil.xyz/verify"
    })
    check("POST /analyze/email", r.status_code, (200,), r.text)
    if r.status_code == 200:
        d = r.json()
        print(f"     {CYAN}↳ Risk: {d.get('risk_score')} | Level: {d.get('threat_level')}{RESET}")

# ─── Users ────────────────────────────────────────────────────────────────────
section("5. USERS")
with httpx.Client(base_url=BASE, timeout=15) as c:
    r = c.get(f"{API}/users", headers=headers)
    check("GET /users", r.status_code, (200,))

# ─── Gmail ────────────────────────────────────────────────────────────────────
section("6. GMAIL (OAuth required)")
with httpx.Client(base_url=BASE, timeout=15) as c:
    r = c.get(f"{API}/gmail/status", headers=headers)
    check("GET /gmail/status", r.status_code, (200, 404))

# ─── Remote ───────────────────────────────────────────────────────────────────
section("7. REMOTE")
with httpx.Client(base_url=BASE, timeout=15) as c:
    r = c.get(f"{API}/remote/status", headers=headers)
    check("GET /remote/status", r.status_code, (200, 404))

# ─── API Docs ─────────────────────────────────────────────────────────────────
section("8. API DOCUMENTATION")
with httpx.Client(base_url=BASE, timeout=10) as c:
    r = c.get("/docs")
    check("GET /docs (Swagger UI)", r.status_code, (200,))
    r = c.get("/openapi.json")
    check("GET /openapi.json", r.status_code, (200,))

# ─── Summary ──────────────────────────────────────────────────────────────────
total = len(passed) + len(failed)
print(f"\n{BOLD}{'═'*55}{RESET}")
print(f"{BOLD}  RESULTS: {GREEN}{len(passed)} passed{RESET}  {RED}{len(failed)} failed{RESET}  / {total} total{RESET}")
print(f"{BOLD}{'═'*55}{RESET}")
if failed:
    print(f"\n{RED}{BOLD}  Failed endpoints:{RESET}")
    for f in failed:
        print(f"  {RED}  • {f}{RESET}")
print()
