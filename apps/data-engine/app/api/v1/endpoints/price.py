from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.price_monitor import PriceMonitor as PriceMonitorSchema, PriceMonitorCreate
from app.schemas.search import SearchRequest
from app.services.price_service import PriceMonitorService
from app.services.search_service import SearchService
from app.api.v1.deps import PermissionChecker
from app.utils.responses import response_success

router = APIRouter(
    prefix="/prices", 
    tags=["prices"],
    dependencies=[Depends(PermissionChecker(["AC_100010"]))]
)
price_monitor_service = PriceMonitorService()
search_service = SearchService()


@router.get("")
def read_prices(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve price monitors."""
    monitors = price_monitor_service.list_monitors(db, skip=skip, limit=limit)
    data = [PriceMonitorSchema.model_validate(m) for m in monitors]
    return response_success(data)


@router.post("")
def create_price(
    *,
    db: Session = Depends(get_db),
    price_in: PriceMonitorCreate,
) -> Any:
    """Create new price monitor."""
    monitor = price_monitor_service.create_monitor(db, price_in.model_dump())
    return response_success(PriceMonitorSchema.model_validate(monitor))


@router.post("/search")
def search_prices(payload: SearchRequest) -> Any:
    """Search price monitors with Elasticsearch when enabled."""
    if not search_service.is_enabled():
        return response_success({
            "enabled": False,
            "items": [],
        }, "Elasticsearch is disabled. Set DATA_ENGINE_ENABLE_ELASTICSEARCH=true to enable search.")
    
    return response_success({
        "enabled": True,
        "items": search_service.search_monitors(payload.query, limit=payload.limit),
    })


@router.get("/compare/{product_id}")
async def compare_prices(product_id: str):
    """Compare prices across platforms for a product."""
    # Mock data for frontend alignment
    data = [
        {"platform": "JD", "price": 4999.00, "final_price": 4899.00},
        {"platform": "Tmall", "price": 5099.00, "final_price": 4999.00},
        {"platform": "Pinduoduo", "price": 4899.00, "final_price": 4799.00},
    ]
    return response_success(data)


@router.get("/trend/{product_id}")
async def get_price_trend(product_id: str, range: str = "30d"):
    """Get price trend data for a product."""
    # Mock data for frontend alignment
    data = [
        {"date": "2026-03-17", "price": 5200.00},
        {"date": "2026-03-24", "price": 5100.00},
        {"date": "2026-03-31", "price": 4999.00},
        {"date": "2026-04-07", "price": 5050.00},
        {"date": "2026-04-14", "price": 4999.00},
    ]
    return response_success(data)


@router.get("/history-low/{product_id}")
async def get_history_low(product_id: str):
    """Get historical lowest price for a product."""
    # Mock data for frontend alignment
    data = {
        "product_id": product_id,
        "lowest_price": 4799.00,
        "date": "2025-11-11",
        "platform": "Pinduoduo"
    }
    return response_success(data)
