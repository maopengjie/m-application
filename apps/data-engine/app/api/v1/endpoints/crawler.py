from fastapi import APIRouter

from app.schemas.crawler import CrawlerStartPayload
from app.services.crawler_service import CrawlerService
from app.utils.responses import response_success

router = APIRouter(prefix="/crawler", tags=["crawler"])
crawler_service = CrawlerService()


@router.post("/start")
async def start_crawler(payload: CrawlerStartPayload):
    result = crawler_service.start_crawler(payload.target_url)
    return response_success(result, "Crawler task started")
