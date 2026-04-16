from datetime import datetime
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class PriceAlertCreate(BaseModel):
    sku_id: int
    target_price: Decimal
    user_id: int = 1  # Default for MVP


class PriceAlertResponse(PriceAlertCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    model_config = ConfigDict(from_attributes=True)
