from typing import Any
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
    limit: int = 20,
    db: Session = Depends(get_db),
) -> Any:
    """Search products across the platform."""
    results = product_service.search_products(db, q, limit)
    
    items = []
    for p, min_price in results:
        items.append(ProductSearchResult(
            id=p.id,
            name=p.name,
            main_image=p.main_image,
            brand=p.brand,
            min_price=min_price
        ))
        
    return SearchResponse(items=items, total=len(items))
