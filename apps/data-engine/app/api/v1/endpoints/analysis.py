from fastapi import APIRouter

from app.services.analysis_service import AnalysisService
from app.utils.responses import response_success
from app.api.v1.deps import get_current_user
from fastapi import Depends

router = APIRouter(
    prefix="/analysis", 
    tags=["analysis"],
    dependencies=[Depends(get_current_user)]
)
analysis_service = AnalysisService()


@router.get("/summary")
async def get_analysis():
    return response_success(analysis_service.get_summary())
