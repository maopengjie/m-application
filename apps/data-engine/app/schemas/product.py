from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class PriceHistoryBase(BaseModel):
    price: Decimal
    recorded_at: datetime


class PriceHistory(PriceHistoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CouponBase(BaseModel):
    type: str
    amount: Decimal
    condition_amount: Optional[Decimal] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


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

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    main_image: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    skus: List[ProductSKU] = []

    model_config = ConfigDict(from_attributes=True)


class PriceHistoryStats(BaseModel):
    history: List[PriceHistoryBase]
    min_price: float
    max_price: float
    avg_price: float
    current_price: float
