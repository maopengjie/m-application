from fastapi import APIRouter

from app.schemas.crawler import CrawlerStartPayload, CrawlPreviewPayload
from app.services.crawler_service import CrawlerService
from app.utils.responses import response_success

router = APIRouter(prefix="/crawler", tags=["crawler"])
crawler_service = CrawlerService()


@router.post("/start")
async def start_crawler(payload: CrawlerStartPayload):
    result = crawler_service.start_crawler(payload.target_url)
    return response_success(result, "Crawler task started")


@router.post("/trigger-update")
async def trigger_update():
    from app.core.database import SessionLocal
    from app.services.collector_service import CollectorService
    
    db = SessionLocal()
    try:
        service = CollectorService()
        count = service.run_collection(db)
        return {"message": "Price update task completed", "updates_count": count}
    finally:
        db.close()
