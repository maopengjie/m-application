import os
import sys

# Add the project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.core.database import SessionLocal
from app.models.user import User

def fix_user_path():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "vben").first()
        if user:
            print(f"Updating user {user.username} home_path from {user.home_path} to /commerce/home")
            user.home_path = "/commerce/home"
            db.commit()
            print("Successfully updated.")
        else:
            print("User vben not found.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_path()
