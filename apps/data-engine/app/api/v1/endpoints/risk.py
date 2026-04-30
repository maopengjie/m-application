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
    results = db.query(RiskScore, ProductSKU).join(ProductSKU, RiskScore.sku_id == ProductSKU.id).filter(RiskScore.score >= min_score).order_by(RiskScore.updated_at.desc()).limit(limit).all()
    
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


@router.post("/scan")
async def scan_product_risk(
    product_url: str,
    db: Session = Depends(get_db)
) -> Any:
    """Simulate AI scanning of a new product URL for risks."""
    import random
    import time
    
    # Simulate processing time
    time.sleep(1.5)
    
    # Mock AI logic: generate a result based on URL or random
    score = random.randint(35, 98)
    
    platform = "JD"
    if "tmall" in product_url.lower() or "taobao" in product_url.lower():
        platform = "Tmall"
    elif "pinduoduo" in product_url.lower():
        platform = "Pinduoduo"
        
    result = {
        "id": int(time.time()),
        "sku_title": f"扫描商品: {product_url[:30]}...",
        "platform": platform,
        "score": score,
        "comment_abnormal": score < 60,
        "sales_abnormal": score < 45,
        "updated_at": "刚刚"
    }
    
    return response_success(result)
