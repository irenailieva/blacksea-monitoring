from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def seed():
    db = SessionLocal()
    try:
        username = "admin"
        if not db.query(User).filter(User.username == username).first():
            user = User(
                username=username,
                email="admin@example.com",
                password_hash=hash_password("admin"),
                role="admin"
            )
            db.add(user)
            db.commit()
            print("User 'admin' created successfully.")
        else:
            print("User 'admin' already exists.")
    except Exception as e:
        print(f"Error seeding user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
