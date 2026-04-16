from typing import List, Optional
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class ProductSearchResult(BaseModel):
    product_id: int
    name: str
    image: Optional[str] = None
    brand: Optional[str] = None
    platform: Optional[str] = None
    category: Optional[str] = None
    min_price: float
    final_price: Optional[float] = None
    shop_name: Optional[str] = None
    platform_count: int = 1
    comments_count: int = 0
    tags: List[str] = []


class SearchResponse(BaseModel):
    items: List[ProductSearchResult]
    total: int
