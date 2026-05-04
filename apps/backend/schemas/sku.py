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
