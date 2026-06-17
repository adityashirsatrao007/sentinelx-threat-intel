import sys
sys.path.insert(0, "/Users/surajbayas/Developer/SentinelX/backend")

from app.database.session import SessionLocal
from app.database.models.models import User
from app.core.security import hash_password

def reset_password():
    db = SessionLocal()
    try:
        from app.core.security import hash_password
        pwd_hash = hash_password("Admin@2025")
    except ImportError:
        # Maybe it's get_password_hash
        from app.core.security import get_password_hash
        pwd_hash = get_password_hash("Admin@2025")
        
    try:
        user = db.query(User).filter(User.email == "soc@sentinelx.com").first()
        if user:
            user.hashed_password = pwd_hash
            db.commit()
            print("Password for soc@sentinelx.com has been reset to: Admin@2025")
        else:
            print("User soc@sentinelx.com not found!")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
