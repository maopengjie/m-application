from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    real_name = Column(String(100))
    roles = Column(JSON, default=list)  # List of strings e.g., ["admin", "user"]
    home_path = Column(String(255), default="/dashboard")
    
    # Audit and Status fields
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "realName": self.real_name,
            "roles": self.roles,
            "homePath": self.home_path,
            "isActive": self.is_active,
            "isLocked": self.is_locked,
            "lastLoginAt": self.last_login_at.isoformat() if self.last_login_at else None,
        }
