from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password
import bcrypt

def debug_login():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("User 'admin' not found!")
            return

        print(f"Stored hash: {user.password_hash}")
        
        candidates = ["admin", "admin123"]
        for p in candidates:
            try:
                # Manually try bcrypt check
                is_valid = bcrypt.checkpw(p.encode('utf-8'), user.password_hash.encode('utf-8'))
                print(f"Direct bcrypt check for '{p}': {is_valid}")
                
                # Try security module wrapper
                is_valid_wrap = verify_password(p, user.password_hash)
                print(f"Wrapper verify_password for '{p}': {is_valid_wrap}")
            except Exception as e:
                print(f"Error checking '{p}': {e}")

    finally:
        db.close()

if __name__ == "__main__":
    debug_login()
