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


@router.post("/preview")
async def preview_crawler(payload: CrawlPreviewPayload):
    result = crawler_service.fetch_page(
        payload.target_url,
        dynamic=payload.dynamic,
        selector=payload.selector,
    )
    return response_success(result, "Crawler preview fetched")
