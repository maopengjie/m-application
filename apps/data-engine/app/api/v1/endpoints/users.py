from fastapi import APIRouter, Header, Response

from app.services.auth_service import AuthService
from app.utils.responses import response_error, response_success

router = APIRouter(prefix="/user", tags=["user"])
auth_service = AuthService()


@router.get("/info")
async def get_user_info(response: Response, authorization: str | None = Header(default=None)):
    user = auth_service.get_user_from_access_token(authorization)
    if not user:
        response.status_code = 401
        return response_error("Unauthorized Exception", "Unauthorized Exception")
    return response_success(user)
