from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.search import SearchResponse, ProductSearchResult
from app.services.product_service import ProductService

router = APIRouter(prefix="/search", tags=["search"])
product_service = ProductService()


@router.get("", response_model=SearchResponse)
def search_products(
    q: str = Query(..., min_length=1),
    sort_by: Optional[str] = Query(None), # price_asc, price_desc
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Any:
    """Search products across the platform."""
    # We fetch more in repo to allow for better in-memory filtering/sorting if needed, 
    # but for true pagination we should let the repo handle it.
    results = product_service.search_products(db, q, limit=limit, skip=skip)
    
    items = []
    for p, min_price in results:
        # Calculate the actual min final price among all SKUs
        final_min_price = min([sku.final_price for sku in p.skus]) if p.skus else min_price
        
        items.append(ProductSearchResult(
            id=p.id,
            name=p.name,
            main_image=p.main_image,
            brand=p.brand,
            min_price=min_price,
            final_price=final_min_price
        ))
    
    # Apply sorting in memory for MVP
    if sort_by == 'price_asc':
        items.sort(key=lambda x: x.final_price or x.min_price)
    elif sort_by == 'price_desc':
        items.sort(key=lambda x: x.final_price or x.min_price, reverse=True)
        
    return SearchResponse(items=items, total=len(items))
