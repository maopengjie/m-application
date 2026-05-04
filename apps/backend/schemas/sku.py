from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: object | None = None


class SkuTagSchema(BaseModel):
    id: int
    tag_code: str
    tag_name: str
    tag_type: str
    source_type: str | None = None
    tag_value: str | None = None


class SkuAttributeSchema(BaseModel):
    id: int
    attr_group: str | None = None
    attr_name: str
    attr_value: str
    attr_unit: str | None = None


class SkuProductListItemSchema(BaseModel):
    id: int
    platform: str
    sku_id: str
    product_name: str
    normalized_name: str | None = None
    brand_name: str | None = None
    main_image_url: str | None = None
    category_level_1: str | None = None
    category_level_2: str | None = None
    category_level_3: str | None = None
    shop_name: str | None = None
    status: int
    updated_at: str
    tags: list[SkuTagSchema] = Field(default_factory=list)


class SkuProductDetailSchema(SkuProductListItemSchema):
    category_id_3: int | None = None
    product_url: str | None = None
    attributes: list[SkuAttributeSchema] = Field(default_factory=list)


class SkuProductListDataSchema(BaseModel):
    items: list[SkuProductListItemSchema]
    total: int
    page: int
    page_size: int


class SkuProductQuerySchema(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = None
    brand_name: str | None = None
    platform: str | None = None
    tag_code: str | None = None
    status: Literal[-1, 0, 1] | None = None


class PriceTimeSeriesQuerySchema(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = None
    platform: str | None = None
    status: Literal[-1, 0, 1] | None = None


class PriceTimeSeriesSummarySchema(BaseModel):
    active_promotion_count: int
    avg_discount_rate: float
    lowest_price_sku_count: int
    total_sku_count: int
    total_snapshot_count: int


class PriceTimeSeriesListItemSchema(BaseModel):
    average_price: float
    brand_name: str | None = None
    capture_count: int
    current_price: float
    highest_price: float
    id: int
    latest_capture_at: str
    lowest_price: float
    main_image_url: str | None = None
    platform: str
    product_name: str
    recent_promo_text: str | None = None
    shop_name: str | None = None
    sku_id: str
    status: int


class PriceTimeSeriesListDataSchema(BaseModel):
    items: list[PriceTimeSeriesListItemSchema]
    page: int
    page_size: int
    summary: PriceTimeSeriesSummarySchema
    total: int


class PriceSnapshotSchema(BaseModel):
    captured_at: str
    final_price: float
    is_historical_low: bool
    list_price: float
    promo_text: str | None = None


class PromotionRecordSchema(BaseModel):
    captured_at: str
    coupon_amount: float
    final_price: float
    formula: str
    list_price: float
    other_discount_amount: float
    promo_text: str | None = None
    reduction_amount: float


class PriceExtremesSchema(BaseModel):
    average_price: float
    current_price: float
    highest_price: float
    highest_price_at: str
    lowest_price: float
    lowest_price_at: str
    price_span: float


class PriceTimeSeriesDetailSchema(BaseModel):
    price_extremes: PriceExtremesSchema
    product: PriceTimeSeriesListItemSchema
    promotion_records: list[PromotionRecordSchema]
    timeline: list[PriceSnapshotSchema]


class SkuImportAttributeSchema(BaseModel):
    attr_group: str | None = None
    attr_name: str
    attr_unit: str | None = None
    attr_value: str
    source_text: str | None = None


class SkuImportTagSchema(BaseModel):
    tag_code: str | None = None
    tag_name: str
    tag_type: str | None = None
    description: str | None = None
    source_type: str | None = None
    tag_value: str | None = None


class SkuImportPriceSchema(BaseModel):
    captured_at: str = Field(..., description="抓取时间，ISO格式")
    list_price: int = Field(..., description="标价，单位分")
    reduction_amount: int = Field(default=0, description="满减金额，单位分")
    coupon_amount: int = Field(default=0, description="优惠券金额，单位分")
    other_discount_amount: int = Field(default=0, description="其他优惠金额，单位分")
    final_price: int = Field(..., description="到手价，单位分")
    promo_text: str | None = Field(default=None, description="促销文案")


class SkuImportPayloadSchema(BaseModel):
    platform: str = "jd"
    sku_id: str
    product_name: str
    normalized_name: str | None = None
    brand_name: str | None = None
    main_image_url: str | None = None
    category_level_1: str | None = None
    category_level_2: str | None = None
    category_level_3: str | None = None
    category_id_3: int | None = None
    shop_name: str | None = None
    product_url: str | None = None
    status: int = 1
    attributes: list[SkuImportAttributeSchema] = Field(default_factory=list)
    tags: list[SkuImportTagSchema] = Field(default_factory=list)
    prices: list[SkuImportPriceSchema] = Field(default_factory=list)
