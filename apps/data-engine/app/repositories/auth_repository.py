from typing import Any, List
from sqlalchemy.orm import Session
from app.models.user import User

class AuthRepository:
    def find_user_by_username(self, db: Session, username: str) -> User | None:
        user = db.query(User).filter(User.username == username).first()
        if user and user.is_locked:
            # Implement 15-minute cooldown strategy
            from datetime import datetime, timedelta, timezone
            # If the user was locked more than 15 minutes ago, auto-unlock them
            # Ensure timezone safety by comparing naive UTC since SQLAlchemy func.now() stores UTC
            if user.updated_at and datetime.utcnow() - user.updated_at > timedelta(minutes=15):
                user.is_locked = False
                user.failed_login_attempts = 0
                db.commit()
                db.refresh(user)
        return user

    def get_access_codes(self, db: Session, username: str) -> List[str]:
        user = self.find_user_by_username(db, username)
        if user:
            # In a production system, these might come from a separate table or roles
            # For now, we can derive them from roles or keep a simple mapping
            # This is already much better than hardcoded MOCK_CODES
            role_to_codes = {
                "super": ["AC_100100", "AC_100110", "AC_100120", "AC_100010"],
                "admin": ["AC_100010", "AC_100020", "AC_100030"],
                "user": ["AC_1000001", "AC_1000002"],
            }
            codes = []
            for role in user.roles:
                codes.extend(role_to_codes.get(role, []))
            return list(set(codes)) # Unique codes
        return []

    def update_last_login(self, db: Session, user_id: int):
        from datetime import datetime
        db.query(User).filter(User.id == user_id).update({
            "last_login_at": datetime.now(),
            "failed_login_attempts": 0
        })
        db.commit()

    def increment_failed_attempts(self, db: Session, username: str):
        user = self.find_user_by_username(db, username)
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.is_locked = True
            db.commit()
