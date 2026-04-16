from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class PriceAlertCreate(BaseModel):
    sku_id: int
    target_price: Decimal
    user_id: int = 1  # Default for MVP


class PriceAlertResponse(PriceAlertCreate):
    id: int
    created_at: datetime
    product_title: str
    product_image: Optional[str] = None
    current_price: Decimal
    notify_methods: list[str] = ["web"]
    
    model_config = ConfigDict(from_attributes=True)
