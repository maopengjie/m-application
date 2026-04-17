from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.schemas.crawler import CrawlerStartPayload, CrawlPreviewPayload, CrawlTaskResponse
from app.services.crawler_service import CrawlerService
from app.services.collector_service import CollectorService
from app.utils.responses import response_success
from app.api.v1.deps import PermissionChecker
from app.core.database import get_db, SessionLocal
from app.models.task import CrawlTask
from app.models.platform_health import PlatformHealth
from app.models.product import ProductSKU

# Require admin or super code for all crawler operations
router = APIRouter(
    prefix="/crawler", 
    tags=["crawler"],
    dependencies=[Depends(PermissionChecker(["AC_100010"]))]
)
crawler_service = CrawlerService()


@router.post("/start")
async def start_crawler(
    payload: CrawlerStartPayload,
    db: Session = Depends(get_db)
):
    result = crawler_service.start_crawler(db, payload.target_url)
    return response_success(result, "Crawler task started")


@router.get("/tasks")
async def get_tasks(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    tasks = db.query(CrawlTask).order_by(CrawlTask.start_time.desc()).offset(skip).limit(limit).all()
    data = [CrawlTaskResponse.model_validate(t) for t in tasks]
    return response_success(data)


@router.get("/results")
async def get_scraping_results(
    skip: int = 0,
    limit: int = 50,
    platform: str = None,
    db: Session = Depends(get_db)
):
    """Returns a list of all processed SKU data from the data engine."""
    query = db.query(ProductSKU)
    if platform:
        query = query.filter(ProductSKU.platform == platform)
    
    results = (
        query.order_by(ProductSKU.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return response_success(results)


@router.post("/trigger-update")
async def trigger_update(db: Session = Depends(get_db)):
    """
    Manually triggers a price collection run.
    Uses a background thread to avoid blocking the API response.
    """
    import threading
    
    # 1. Check for overlapping tasks
    active_task = db.query(CrawlTask).filter(CrawlTask.status == "running").first()
    if active_task:
        raise HTTPException(status_code=409, detail="A price update task is already running")

    count = db.query(ProductSKU).count()
    service = CollectorService()
    
    # 2. Fire and forget in background
    def background_run():
        new_db = SessionLocal()
        try:
            service.run_collection(new_db)
        finally:
            new_db.close()

    thread = threading.Thread(target=background_run)
    thread.daemon = True
    thread.start()
    
    return response_success({"updates_count": count}, "Price update task triggered in background")


@router.get("/platform-health")
async def get_platform_health(db: Session = Depends(get_db)):
    """Returns the latest health snapshot for each platform."""
    
    # Subquery to find the latest timestamp per platform
    last_snapshots = (
        db.query(PlatformHealth.platform, func.max(PlatformHealth.timestamp).label("max_ts"))
        .group_by(PlatformHealth.platform)
        .subquery()
    )
    
    # Join with the full model to get latest records
    health_data = (
        db.query(PlatformHealth)
        .join(last_snapshots, (PlatformHealth.platform == last_snapshots.c.platform) & 
                             (PlatformHealth.timestamp == last_snapshots.c.max_ts))
        .all()
    )
    
    return response_success(health_data)


@router.get("/platform-health/trends")
async def get_health_trends(
    days: int = 7, 
    db: Session = Depends(get_db)
):
    """Returns historical health trends for all platforms."""
    since = datetime.now() - timedelta(days=days)
    trends = (
        db.query(PlatformHealth)
        .filter(PlatformHealth.timestamp >= since)
        .order_by(PlatformHealth.platform, PlatformHealth.timestamp.asc())
        .all()
    )
    
    # Simple grouping for the frontend
    result = {}
    for t in trends:
        if t.platform not in result:
            result[t.platform] = []
        result[t.platform].append({
            "ts": t.timestamp,
            "success": t.success_count,
            "failed": t.failed_count,
            "latency": t.avg_latency_ms,
            "status": t.status
        })
        
    return response_success(result)


@router.get("/smoke-status")
async def get_smoke_status(db: Session = Depends(get_db)):
    """Specialized health status summarizing the very last check across all metrics."""
    latest_global = db.query(PlatformHealth).order_by(desc(PlatformHealth.timestamp)).limit(5).all()
    
    summary = {
        "is_all_healthy": all(p.status == "healthy" for p in latest_global) if latest_global else True,
        "critical_platforms": [p.platform for p in latest_global if p.status == "critical"],
        "last_check_at": latest_global[0].timestamp if latest_global else None
    }
    
    return response_success(summary)
