from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class PriceAlertCreate(BaseModel):
    sku_id: int
    target_price: Decimal
    user_id: int = 1  # Default for MVP
    notify_methods: Optional[str] = "web" # Comma separated: web,email,sms
    email: Optional[str] = None
    phone: Optional[str] = None


class AlertProductInfo(BaseModel):
    id: int
    name: str
    main_image: Optional[str] = None
    brand: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AlertSkuInfo(BaseModel):
    id: int
    product_id: int
    platform: str
    price: float
    shop_name: Optional[str] = None
    buy_url: Optional[str] = None
    product: AlertProductInfo

    model_config = ConfigDict(from_attributes=True)


class PriceAlertResponse(PriceAlertCreate):
    id: int
    is_triggered: bool
    status: str
    triggered_at: Optional[datetime] = None
    triggered_price: Optional[float] = None
    current_price: Optional[float] = None
    trigger_reason: Optional[str] = None
    created_at: datetime
    sku: Optional[AlertSkuInfo] = None
    
    model_config = ConfigDict(from_attributes=True)

