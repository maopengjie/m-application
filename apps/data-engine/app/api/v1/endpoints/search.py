from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.search import SearchResponse, ProductSearchResult
from app.services.product_service import ProductService
from app.api.v1.deps import get_current_user
from app.utils.responses import response_success

router = APIRouter(
    prefix="/search", 
    tags=["search"],
    dependencies=[Depends(get_current_user)]
)
product_service = ProductService()


@router.get("")
def search_products(
    q: str = Query(..., min_length=1),
    sort_by: Optional[str] = Query(None), # price_asc, price_desc
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    platforms: Optional[List[str]] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Any:
    """Search products across the platform."""
    results, total_count = product_service.search_products(
        db, 
        q, 
        limit=limit, 
        skip=skip,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        platforms=platforms,
        sort_by=sort_by
    )
    
    items = []
    for p, current_min_price in results:
        # Step 1: Isolate the applicable SKUs based on the platform filter from the request
        valid_skus = [s for s in p.skus if s.platform in platforms] if platforms else p.skus
        
        # Calculate the actual min final price among valid SKUs
        final_prices = [sku.final_price for sku in valid_skus]
        final_min_price = min(final_prices) if final_prices else current_min_price
        
        # Calculate unique platforms among valid SKUs
        platforms_found = set([sku.platform for sku in valid_skus])
        
        # Generate tags based on valid SKUs
        tags = []
        if len(platforms_found) > 1:
            tags.append("多平台比价")
        if final_min_price < current_min_price * 0.9:
            tags.append("大额优惠")
        if p.brand == brand:
            tags.append("品牌自营")
            
        # Find the SKU that has the lowest final price among the valid SKUs
        min_price_sku = min(valid_skus, key=lambda s: s.final_price) if valid_skus else None

        # Using dict instead of pydantic model for simplicity in response_success
        items.append({
            "product_id": p.id,
            "name": p.name,
            "image": p.main_image,
            "brand": p.brand,
            "category": p.category,
            "platform": list(platforms_found)[0] if len(platforms_found) == 1 else None,
            "min_price": float(current_min_price),
            "final_price": float(final_min_price),
            "shop_name": min_price_sku.shop_name if min_price_sku else None,
            "platform_count": len(platforms_found),
            "comments_count": sum([len(sku.reviews) for sku in valid_skus]),
            "tags": tags
        })
        
    return response_success({
        "items": items,
        "total": total_count
    })
