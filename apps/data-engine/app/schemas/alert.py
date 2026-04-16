from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class PriceAlertCreate(BaseModel):
    sku_id: int
    target_price: Decimal
    user_id: int = 1  # Default for MVP


class AlertProductInfo(BaseModel):
    id: int
    name: str
    main_image: Optional[str] = None
    brand: Optional[str] = None


class AlertSkuInfo(BaseModel):
    id: int
    platform: str
    price: float
    shop_name: Optional[str] = None
    product: AlertProductInfo


class PriceAlertResponse(PriceAlertCreate):
    id: int
    is_triggered: bool
    status: str
    triggered_at: Optional[datetime] = None
    triggered_price: Optional[float] = None
    created_at: datetime
    sku: Optional[AlertSkuInfo] = None
    
    model_config = ConfigDict(from_attributes=True)
