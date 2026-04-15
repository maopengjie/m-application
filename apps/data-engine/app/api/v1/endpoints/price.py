from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.price_monitor import PriceMonitor as PriceMonitorSchema, PriceMonitorCreate
from app.schemas.search import SearchRequest
from app.services.price_service import PriceMonitorService
from app.services.search_service import SearchService

router = APIRouter(prefix="/prices", tags=["prices"])
price_monitor_service = PriceMonitorService()
search_service = SearchService()


@router.get("", response_model=list[PriceMonitorSchema])
def read_prices(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve price monitors."""
    return price_monitor_service.list_monitors(db, skip=skip, limit=limit)


@router.post("", response_model=PriceMonitorSchema)
def create_price(
    *,
    db: Session = Depends(get_db),
    price_in: PriceMonitorCreate,
) -> Any:
    """Create new price monitor."""
    return price_monitor_service.create_monitor(db, price_in.model_dump())


@router.post("/search")
def search_prices(payload: SearchRequest) -> Any:
    """Search price monitors with Elasticsearch when enabled."""
    if not search_service.is_enabled():
        return {
            "enabled": False,
            "items": [],
            "message": "Elasticsearch is disabled. Set DATA_ENGINE_ENABLE_ELASTICSEARCH=true to enable search.",
        }
    return {
        "enabled": True,
        "items": search_service.search_monitors(payload.query, limit=payload.limit),
    }
