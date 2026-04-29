from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class PriceHistoryBase(BaseModel):
    price: Decimal
    recorded_at: datetime


class PriceHistory(PriceHistoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CouponBase(BaseModel):
    title: str
    desc: Optional[str] = None
    type: str
    amount: Decimal
    condition_amount: Optional[Decimal] = None


class Coupon(CouponBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ReviewBase(BaseModel):
    rating: int
    content: Optional[str] = None
    created_at: datetime


class Review(ReviewBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RiskScoreBase(BaseModel):
    score: int
    comment_abnormal: bool = False
    sales_abnormal: bool = False
    price_abnormal: bool = False
    rating_low: bool = False
    details: List[str] = []
    updated_at: datetime


class RiskScore(RiskScoreBase):
    model_config = ConfigDict(from_attributes=True)


class ProductSKUBase(BaseModel):
    platform: str
    platform_sku_id: str
    title: str
    price: Decimal
    original_price: Optional[Decimal] = None
    shop_name: Optional[str] = None
    buy_url: Optional[str] = None
    is_official: bool = False


class ProductSKUCreate(ProductSKUBase):
    pass


class ProductSKU(ProductSKUBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime
    price_history: List[PriceHistory] = []
    coupons: List[Coupon] = []
    reviews: List[Review] = []
    risk_score: Optional[RiskScore] = None
    final_price: Optional[float] = None
    promotions: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    main_image: Optional[str] = None
    rating: Optional[float] = 4.5


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    skus: List[ProductSKU] = []
    min_price: Optional[float] = None
    final_price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class PriceHistoryStats(BaseModel):
    history: List[PriceHistoryBase]
    min_price: float
    max_price: float
    avg_price: float
    current_price: float


class ProductFollowCreate(BaseModel):
    product_id: int


class ProductFollow(BaseModel):
    id: int
    user_id: int
    product_id: int
    product: Product
    created_at: datetime
    price_change_percent: Optional[float] = None
    risk_status: Optional[str] = None
    is_near_low: bool = False
    current_status_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(BaseModel):
    product: Product
    is_followed: bool = False
    is_alert_set: bool = False
    active_alert_count: int = 0
    revisit_summary: Optional[Dict[str, Any]] = None  # { "title": "...", "content": "...", "type": "info/warning/success" }
    
    model_config = ConfigDict(from_attributes=True)



class InsightEvent(BaseModel):
    id: str  # Generated ID like "follow_123" or "alert_456"
    product_id: int
    sku_id: Optional[int] = None
    event_type: str  # PRICE_DROP, ALERT_HIT, NEAR_TARGET, HIST_LOW, RISK_CHANGE, NEW_COUPON
    priority: int  # 0-10, 10 is highest
    title: str
    description: str
    current_price: float
    original_price: Optional[float] = None
    diff_amount: Optional[float] = None
    diff_percent: Optional[float] = None
    image: Optional[str] = None
    platform: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class InsightResponse(BaseModel):
    events: List[InsightEvent]
    total: int
    summary: str  # "Today you have 3 critical updates"


