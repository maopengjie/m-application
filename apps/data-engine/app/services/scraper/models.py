from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

class ScrapeResult(BaseModel):
    """
    Unified result model for all platform scrapers.
    Ensures consistent data structure regardless of the source platform.
    """
    success: bool = False
    platform: str
    sku_id: str
    
    # Core Data
    price: Optional[float] = None
    original_price: Optional[float] = None
    title: Optional[str] = None
    shop_name: Optional[str] = None
    stock_status: Optional[str] = None  # in_stock, out_of_stock, pre_order
    buy_url: Optional[str] = None
    
    # Audit & Debugging
    raw_payload: Optional[Any] = None  # Original HTML or JSON for debugging
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.now)
