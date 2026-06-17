"""
SentinelX Corporate Spear-phishing Seeder (Enron Style)
Populates the database with high-end, realistic corporate threat data.
"""
import httpx
import time

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "demo@sentinelx.com"
PASSWORD = "SecurePassword123!"

CORPORATE_THREATS = [
    {
        "sender": "it.support@company-global.net",
        "subject": "MANDATORY: Security Update for Microsoft 365 OWA",
        "body": "Dear Employee, Our system logs indicate that your Outlook Web Access (OWA) account is running an outdated security protocol. To prevent account suspension and ensure data encryption, you are required to re-authenticate your session through our secure IT portal: https://company-owa-update.com/login. Failure to complete this within 4 hours will result in a temporary lockout of all corporate resources.",
        "target_department": "Engineering",
        "target_role": "Developer"
    },
    {
        "sender": "payroll.hr@corporate-services.online",
        "subject": "Action Required: 2024 Tax Document Verification",
        "body": "Hi, We are finalizing the payroll tax documents for the current fiscal quarter. We noticed a discrepancy in your direct deposit information. Please log in to the HR Portal at http://hr-portal-payroll.tk and verify your bank account details and Social Security Number to ensure your next payment is processed without delay.",
        "target_department": "Finance",
        "target_role": "Accountant"
    },
    {
        "sender": "ceo.executive@global-corp-hq.com",
        "subject": "Confidential: Q3 Strategic Partnership - Urgent Wire Request",
        "body": "I am in a high-level meeting and cannot be reached by phone. We are closing a confidential deal with a new vendor. I need you to process an immediate wire transfer of $128,450 to the following account to secure the contract. Use the emergency fund code 'ALPHA-9'. Account: 9982736410, Routing: 011000015. Please confirm once done. - Sent from my iPhone",
        "target_department": "Executive Office",
        "target_role": "Executive Assistant"
    },
    {
        "sender": "accounts.payable@vendor-solutions.biz",
        "subject": "INVOICE OVERDUE: #INV-2024-8892 - Final Notice",
        "body": "Your payment for invoice #INV-2024-8892 is now 15 days overdue. A late fee of 5% has been applied to the balance of $14,200. Please view the attached invoice details and remit payment immediately to avoid service interruption: http://vendor-portal.biz/pay?id=8892. If payment has already been sent, please disregard this notice.",
        "target_department": "Operations",
        "target_role": "Operations Manager"
    },
    {
        "sender": "legal@company-compliance.net",
        "subject": "URGENT: Legal Compliance Audit - Internal Memo",
        "body": "As part of our annual compliance audit, all senior staff are required to review and sign the updated Confidentiality Agreement. Please visit the legal repository at http://compliance-docs-internal.net/sign and use your corporate credentials to provide your digital signature. This is a mandatory requirement for all employees in the Finance and Legal departments.",
        "target_department": "Legal",
        "target_role": "Legal Counsel"
    },
    {
        "sender": "system.admin@internal-relay.io",
        "subject": "VPN Configuration Update Required",
        "body": "Due to a recent network security upgrade, the old VPN configuration will be deprecated tonight at 11:00 PM. To maintain remote access to the internal network, you must download and install the new VPN profile from: http://vpn-config-internal.io/setup. Enter your username and password when prompted by the installer.",
        "target_department": "IT",
        "target_role": "System Admin"
    },
    {
        "sender": "benefits@hr-global-rewards.com",
        "subject": "New Employee Benefit Enrollment - Limited Time",
        "body": "We are excited to announce a new health and wellness benefit program for all employees. You are eligible for a $500 annual wellness credit. To enroll and claim your credit, please complete the registration form at http://wellness-enrollment-hr.com/form by Friday. You will need to provide your employee ID and date of birth for verification.",
        "target_department": "Marketing",
        "target_role": "Marketing Specialist"
    },
]

def get_token():
    resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]

def seed_corporate_threats(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    created = 0

    print("\n🏢 Seeding corporate spear-phishing threats...")
    for sample in CORPORATE_THREATS:
        try:
            # We need to manually add the target fields to the DB after analysis since the API doesn't take them yet
            # Or better, update the API to take them. For now, we'll just send the email and then we'd need to update the record.
            # But wait, I can just update the backend to auto-detect target_department/role from the body or use a dummy.
            # Actually, let's just update the backend to handle these fields in the request.
            
            resp = httpx.post(f"{BASE_URL}/analyze/email", headers=headers, json=sample, timeout=30)
            if resp.status_code == 200:
                r = resp.json()
                print(f"  ✅ Corporate threat | Risk: {r['risk_score']} | Level: {r['threat_level']} | {sample['subject'][:50]}")
                created += 1
            else:
                print(f"  ⚠️  {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        time.sleep(0.5)

    return created

if __name__ == "__main__":
    print("🚀 SentinelX Corporate Data Seeder")
    print("=" * 40)
    
    try:
        token = get_token()
        print("🔐 Login successful.")
        n = seed_corporate_threats(token)
        print(f"\n✅ Seeding complete! Created {n} corporate threats.")
    except Exception as e:
        print(f"❌ Error: {e}")
