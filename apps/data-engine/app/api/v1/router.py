from fastapi import APIRouter

from app.api.v1.endpoints import analysis, auth, crawler, system, users

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(crawler.router)
api_router.include_router(analysis.router)
