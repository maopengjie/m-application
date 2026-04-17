from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.crawler import CrawlerStartPayload, CrawlPreviewPayload
from app.services.crawler_service import CrawlerService
from app.services.collector_service import CollectorService
from app.utils.responses import response_success
from app.api.v1.deps import PermissionChecker

from app.core.database import get_db

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


@router.post("/trigger-update")
async def trigger_update(db: Session = Depends(get_db)):
    service = CollectorService()
    count = service.run_collection(db)
    return {"message": "Price update task completed", "updates_count": count}
