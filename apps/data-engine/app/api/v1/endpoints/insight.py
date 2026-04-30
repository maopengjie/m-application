from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.services.insight_service import InsightService
from app.utils.responses import response_success


from app.services.product_service import ProductService
from app.services.alert_service import AlertService
from app.services.promotion_service import PromotionService
from app.repositories.product_repository import ProductRepository
from app.repositories.alert_repository import AlertRepository
from app.schemas.product import InsightResponse

router = APIRouter(prefix="/insights", tags=["Insights"], redirect_slashes=False)

def get_insight_service() -> InsightService:
    product_service = ProductService()
    alert_service = AlertService()
    return InsightService(product_service, alert_service)


@router.get("")
async def get_insights(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    service: InsightService = Depends(get_insight_service)
) -> Any:
    """
    获取商品异动聚合信息 (G2-02)
    """
    insights = service.get_aggregated_insights(db, current_user["id"])
    return response_success(insights)


