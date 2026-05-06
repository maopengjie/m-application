from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field


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


class SkuTagUpsertSchema(BaseModel):
    tag_code: str
    tag_name: str | None = None
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
    category_id: int | None = None
    category_level: int | None = None
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
    anomaly_reason: str | None = None
    captured_at: str
    final_price: float
    is_anomalous: bool = False
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
    highest_price_at: str | None = None
    lowest_price: float
    lowest_price_at: str | None = None
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


class CategoryNodeSchema(BaseModel):
    id: int
    platform: str
    external_id: str | None = None
    name: str
    level: int
    parent_id: int | None = None
    path: str | None = None
    sort_order: int
    children: list[CategoryNodeSchema] = Field(default_factory=list)

CategoryNodeSchema.model_rebuild()


class CategoryImportNodeSchema(BaseModel):
    name: str
    external_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("external_id", "id", "category_id", "cid"),
    )
    sort_order: int = 0
    children: list[CategoryImportNodeSchema] = Field(default_factory=list)


CategoryImportNodeSchema.model_rebuild()


class CategoryTreeImportSchema(BaseModel):
    platform: str = "jd"
    nodes: list[CategoryImportNodeSchema]


class MappingRuleSchema(BaseModel):
    id: int
    rule_type: str
    platform: str | None = None
    category_id: int | None = None
    pattern: str
    unified_label: str
    is_active: int
    priority: int
    created_at: str
    updated_at: str


class MappingRuleCreateUpdateSchema(BaseModel):
    rule_type: str = "KEYWORD"
    platform: str | None = None
    category_id: int | None = None
    pattern: str
    unified_label: str
    is_active: int = 1
    priority: int = 0


class SkuComparisonSchema(BaseModel):
    id: int
    master_sku_id: int
    linked_sku_id: int
    match_score: int | None = None
    match_reasons: list[str] = Field(default_factory=list)
    match_type: str
    status: int
    master_sku: SkuProductListItemSchema | None = None
    linked_sku: SkuProductListItemSchema | None = None


class SkuComparisonReviewSchema(BaseModel):
    approved: bool


class ScrapeProductRequestSchema(BaseModel):
    url: str


class ScrapeBatchRequestSchema(BaseModel):
    limit: int = Field(default=20, ge=1, le=200)
    platform: str | None = None


class ScrapeTaskRunSchema(BaseModel):
    id: int
    task_id: str | None = None
    task_name: str
    trigger_source: str
    platform: str | None = None
    requested_limit: int | None = None
    requested_url: str | None = None
    status: str
    processed_count: int
    success_count: int
    failure_count: int
    started_at: str | None = None
    finished_at: str | None = None
    summary_message: str | None = None
    error_message: str | None = None
    failed_items: list[dict[str, object]] = Field(default_factory=list)
    created_at: str
    updated_at: str


class CategoryTreeQuerySchema(BaseModel):
    platform: str = "jd"


class MappingRuleQuerySchema(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = None
    platform: str | None = None


class SkuComparisonQuerySchema(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    master_sku_id: int | None = None
