from fastapi import APIRouter

from app.utils.responses import response_success

router = APIRouter()


@router.get("/status")
async def get_status():
    return response_success(
        {
            "status": "online",
            "engine": "FastAPI",
            "task_count": 0,
        }
    )
