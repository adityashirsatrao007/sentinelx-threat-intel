import sys

# Add the backend directory to sys.path so we can import 'app'
sys.path.insert(0, "/Users/surajbayas/Developer/SentinelX/backend")

from app.database.session import SessionLocal
from app.database.models.models import User

def get_soc_users():
    db = SessionLocal()
    try:
        # UserRole is an enum, we can just filter by the string value or enum
        users = db.query(User).filter(User.role.in_(['soc', 'sysadmin'])).all()
        for u in users:
            print(f"Name: {u.name} | Email: {u.email} | Role: {u.role.value if hasattr(u.role, 'value') else u.role}")
        if not users:
            print("No SOC/sysadmin users found.")
    finally:
        db.close()

if __name__ == "__main__":
    get_soc_users()
