from typing import List, Optional
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class ProductSearchResult(BaseModel):
    id: int
    name: str
    main_image: Optional[str] = None
    brand: Optional[str] = None
    min_price: float


class SearchResponse(BaseModel):
    items: List[ProductSearchResult]
    total: int
