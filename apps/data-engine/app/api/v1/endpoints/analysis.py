from fastapi import APIRouter

from app.services.analysis_service import AnalysisService
from app.utils.responses import response_success

router = APIRouter(prefix="/analysis", tags=["analysis"])
analysis_service = AnalysisService()


@router.get("/summary")
async def get_analysis():
    return response_success(analysis_service.get_summary())
