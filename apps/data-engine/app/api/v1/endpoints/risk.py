from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import RiskScore, ProductSKU
from app.utils.responses import response_success
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/risks", tags=["risks"], dependencies=[Depends(get_current_user)])

@router.get("")
async def list_risks(
    db: Session = Depends(get_db),
    min_score: int = 0,
    limit: int = 50,
) -> Any:
    """List risk scores for monitored products."""
    # Joining with SKU to provide context in the risk view
    results = db.query(RiskScore, ProductSKU).join(ProductSKU, RiskScore.sku_id == ProductSKU.id).filter(RiskScore.score >= min_score).limit(limit).all()
    
    formatted = []
    for risk, sku in results:
        formatted.append({
            "id": risk.sku_id,
            "sku_title": sku.title,
            "platform": sku.platform,
            "score": risk.score,
            "comment_abnormal": risk.comment_abnormal,
            "sales_abnormal": risk.sales_abnormal,
            "updated_at": risk.updated_at
        })
    return response_success(formatted)
