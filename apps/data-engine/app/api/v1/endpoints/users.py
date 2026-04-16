from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, PermissionChecker
from app.core.database import get_db
from app.models.user import User
from app.utils.responses import response_error, response_success

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/info")
async def get_user_info(user: dict = Depends(get_current_user)):
    return response_success(user)


@router.post("/{user_id}/unlock", dependencies=[Depends(PermissionChecker(["AC_100010"]))])
def unlock_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Admin endpoint to manually unlock a locked user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.is_locked:
        return response_success({"message": "User is already unlocked"}, "User is not locked")

    user.is_locked = False
    user.failed_login_attempts = 0
    db.commit()
    
    return response_success({"message": "User successfully unlocked"}, "User unlocked")
