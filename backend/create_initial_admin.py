from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.crud import user as crud_user
from app.schemas import UserCreate
from app.models.user import User

def create_admin():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if user:
            print("Admin user already exists.")
            return

        print("Creating admin user...")
        user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="admin"
        )
        crud_user.create(db=db, obj_in=user_in)
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error creating admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
