from typing import List, Protocol, Any
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User

auth_service = AuthService()

def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None)
) -> dict[str, Any]:
    user = auth_service.get_user_from_access_token(db, authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

class PermissionChecker:
    def __init__(self, required_codes: List[str]):
        self.required_codes = required_codes

    def __call__(
        self, 
        user: dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        user_codes = auth_service.get_access_codes(db, user["username"])
        
        # Check if user has ALL required codes
        # In some systems it might be ANY of the required codes, 
        # but usually more restrictive is better by default.
        for code in self.required_codes:
            if code not in user_codes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required code: {code}",
                )
        return user
