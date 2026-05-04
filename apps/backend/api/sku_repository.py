from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from db.session import get_db
from models import SkuProduct, SkuProductAttr, SkuTagRelation, TagDefinition
from schemas.sku import (
    ApiResponse,
    SkuAttributeSchema,
    SkuProductDetailSchema,
    SkuProductListDataSchema,
    SkuProductListItemSchema,
    SkuProductQuerySchema,
    SkuTagSchema,
)


router = APIRouter(prefix="/sku-repository", tags=["sku-repository"])


def dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def ok(data, message: str = "ok"):
    return dump_model(ApiResponse(code=0, message=message, data=data))


def _serialize_tag_relation(relation: SkuTagRelation, definition: TagDefinition | None) -> SkuTagSchema:
    return SkuTagSchema(
        id=definition.id if definition else relation.tag_id,
        tag_code=definition.tag_code if definition else "",
        tag_name=definition.tag_name if definition else "",
        tag_type=definition.tag_type if definition else "",
        source_type=relation.source_type,
        tag_value=relation.tag_value,
    )


def _build_tag_map(db: Session, product_ids: list[int]) -> dict[int, list[SkuTagSchema]]:
    if not product_ids:
        return {}

    rows = (
        db.query(SkuTagRelation, TagDefinition)
        .join(TagDefinition, TagDefinition.id == SkuTagRelation.tag_id)
        .filter(SkuTagRelation.sku_product_id.in_(product_ids))
        .all()
    )
    result: dict[int, list[SkuTagSchema]] = defaultdict(list)
    for relation, definition in rows:
        result[relation.sku_product_id].append(_serialize_tag_relation(relation, definition))
    return result


@router.get("/products")
def list_products(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    brand_name: str | None = None,
    platform: str | None = None,
    tag_code: str | None = None,
    status: int | None = None,
    db: Session = Depends(get_db),
):
    query_params = SkuProductQuerySchema(
        page=page,
        page_size=page_size,
        keyword=keyword,
        brand_name=brand_name,
        platform=platform,
        tag_code=tag_code,
        status=status,
    )

    query = db.query(SkuProduct)

    if query_params.keyword:
        like_term = f"%{query_params.keyword.strip()}%"
        query = query.filter(
            or_(
                SkuProduct.sku_id.ilike(like_term),
                SkuProduct.product_name.ilike(like_term),
                SkuProduct.normalized_name.ilike(like_term),
            )
        )
    if query_params.brand_name:
        query = query.filter(SkuProduct.brand_name.ilike(f"%{query_params.brand_name.strip()}%"))
    if query_params.platform:
        query = query.filter(SkuProduct.platform == query_params.platform.strip())
    if query_params.status is not None:
        query = query.filter(SkuProduct.status == query_params.status)
    if query_params.tag_code:
        query = (
            query.join(SkuTagRelation, SkuTagRelation.sku_product_id == SkuProduct.id)
            .join(TagDefinition, TagDefinition.id == SkuTagRelation.tag_id)
            .filter(TagDefinition.tag_code == query_params.tag_code.strip())
            .distinct()
        )

    total = query.count()
    products = (
        query.order_by(SkuProduct.updated_at.desc(), SkuProduct.id.desc())
        .offset((query_params.page - 1) * query_params.page_size)
        .limit(query_params.page_size)
        .all()
    )
    product_ids = [item.id for item in products]
    tag_map = _build_tag_map(db, product_ids)

    items = [
        SkuProductListItemSchema(
            id=product.id,
            platform=product.platform,
            sku_id=product.sku_id,
            product_name=product.product_name,
            normalized_name=product.normalized_name,
            brand_name=product.brand_name,
            main_image_url=product.main_image_url,
            category_level_1=product.category_level_1,
            category_level_2=product.category_level_2,
            category_level_3=product.category_level_3,
            shop_name=product.shop_name,
            status=product.status,
            updated_at=product.updated_at.isoformat(sep=" ", timespec="seconds"),
            tags=tag_map.get(product.id, []),
        )
        for product in products
    ]
    payload = SkuProductListDataSchema(
        items=items,
        total=total,
        page=query_params.page,
        page_size=query_params.page_size,
    )
    return ok(dump_model(payload))


@router.get("/products/{product_id}")
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    product = db.query(SkuProduct).filter(SkuProduct.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="SKU product not found")

    attributes = (
        db.query(SkuProductAttr)
        .filter(SkuProductAttr.sku_product_id == product.id)
        .order_by(SkuProductAttr.attr_group.asc(), SkuProductAttr.attr_name.asc())
        .all()
    )
    tag_map = _build_tag_map(db, [product.id])

    payload = SkuProductDetailSchema(
        id=product.id,
        platform=product.platform,
        sku_id=product.sku_id,
        product_name=product.product_name,
        normalized_name=product.normalized_name,
        brand_name=product.brand_name,
        main_image_url=product.main_image_url,
        category_level_1=product.category_level_1,
        category_level_2=product.category_level_2,
        category_level_3=product.category_level_3,
        category_id_3=product.category_id_3,
        shop_name=product.shop_name,
        product_url=product.product_url,
        status=product.status,
        updated_at=product.updated_at.isoformat(sep=" ", timespec="seconds"),
        tags=tag_map.get(product.id, []),
        attributes=[
            SkuAttributeSchema(
                id=item.id,
                attr_group=item.attr_group,
                attr_name=item.attr_name,
                attr_value=item.attr_value,
                attr_unit=item.attr_unit,
            )
            for item in attributes
        ],
    )
    return ok(dump_model(payload))


@router.get("/tags")
def list_tags(db: Session = Depends(get_db)):
    tags = db.query(TagDefinition).order_by(TagDefinition.id.asc()).all()
    payload = [
        dump_model(
            SkuTagSchema(
                id=tag.id,
                tag_code=tag.tag_code,
                tag_name=tag.tag_name,
                tag_type=tag.tag_type,
            )
        )
        for tag in tags
    ]
    return ok(payload)
