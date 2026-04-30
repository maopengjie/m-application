from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, List

from app.services.intelligence_service import IntelligenceService
from app.core.database import get_db
from app.utils.responses import response_success
from app.api.v1.deps import PermissionChecker

router = APIRouter(
    prefix="/intelligence",
    tags=["intelligence"],
    dependencies=[Depends(PermissionChecker(["AC_100010"]))]
)

@router.post("/extract-specs/{product_id}")
async def extract_product_specs(
    product_id: int,
    url: str,
    db: Session = Depends(get_db)
):
    """AI 自动参数提取"""
    intel_service = IntelligenceService(db)
    result = await intel_service.auto_extract_product_attributes(product_id, url)
    if not result: raise HTTPException(status_code=500, detail="AI extraction failed")
    return response_success(result)


@router.post("/analyze-reviews/{sku_id}")
async def analyze_reviews(
    sku_id: int,
    db: Session = Depends(get_db)
):
    """情感与评论分析"""
    intel_service = IntelligenceService(db)
    count = await intel_service.analyze_reviews(sku_id)
    return response_success({"analyzed_count": count})


@router.get("/price-comparison/{product_id}")
async def get_price_comparison(
    product_id: int,
    db: Session = Depends(get_db)
):
    """多平台比价引擎"""
    intel_service = IntelligenceService(db)
    result = intel_service.get_price_comparison(product_id)
    return response_success(result)


@router.get("/inventory-analysis/{sku_id}")
async def get_inventory_analysis(
    sku_id: int,
    db: Session = Depends(get_db)
):
    """获取库存消耗预测分析"""
    intel_service = IntelligenceService(db)
    result = intel_service.predict_restock_needs(sku_id)
    return response_success(result)


@router.get("/pricing-advice/{product_id}")
async def get_pricing_advice(
    product_id: int,
    db: Session = Depends(get_db)
):
    """动态定价建议"""
    intel_service = IntelligenceService(db)
    result = intel_service.suggest_dynamic_pricing(product_id)
    return response_success(result)


@router.get("/product-insight/{product_id}")
async def get_product_insight(
    product_id: int,
    db: Session = Depends(get_db)
):
    """获取 AI 综合情报研判综述"""
    intel_service = IntelligenceService(db)
    result = await intel_service.generate_product_insight(product_id)
    return response_success(result)


@router.get("/market-insights")
async def get_market_insights(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    [2.1 智能化] 获取全网实时市场快报
    """
    intel_service = IntelligenceService(db)
    result = await intel_service.get_market_insights(limit)
    return response_success(result)
