from __future__ import annotations

import re
import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import SkuPriceSnapshot, SkuProduct, SkuProductAttr, SkuTagRelation, TagDefinition


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def _build_tag_code(tag_name: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", tag_name.upper()).strip("_")
    return cleaned or "CUSTOM_TAG"


def _normalize_attr(item: dict[str, Any]) -> dict[str, str | None]:
    attr_name = _clean_text(item.get("attr_name") or item.get("name"))
    attr_value = _clean_text(item.get("attr_value") or item.get("value"))
    if not attr_name or not attr_value:
        return {}
    return {
        "attr_group": _clean_text(item.get("attr_group") or item.get("group")) or "主体",
        "attr_name": attr_name,
        "attr_value": attr_value,
        "attr_unit": _clean_text(item.get("attr_unit") or item.get("unit")),
        "source_text": _clean_text(item.get("source_text")),
    }


def _ensure_tag_definition(db: Session, tag_item: dict[str, Any]) -> TagDefinition | None:
    tag_name = _clean_text(tag_item.get("tag_name") or tag_item.get("name"))
    if not tag_name:
        return None

    tag_code = _clean_text(tag_item.get("tag_code") or tag_item.get("code")) or _build_tag_code(tag_name)
    tag_type = _clean_text(tag_item.get("tag_type") or tag_item.get("type")) or "SYSTEM"
    description = _clean_text(tag_item.get("description"))

    tag = db.query(TagDefinition).filter(TagDefinition.tag_code == tag_code).first()
    if tag is None:
        tag = TagDefinition(
            tag_code=tag_code,
            tag_name=tag_name,
            tag_type=tag_type,
            description=description,
        )
        db.add(tag)
        db.flush()
        return tag

    tag.tag_name = tag_name
    tag.tag_type = tag_type
    if description:
        tag.description = description
    return tag


def ingest_sku_payload(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    platform = _clean_text(payload.get("platform")) or "jd"
    sku_id = _clean_text(payload.get("sku_id"))
    if not sku_id:
        raise ValueError("sku_id is required for SKU ingestion")

    product = (
        db.query(SkuProduct)
        .filter(SkuProduct.platform == platform, SkuProduct.sku_id == sku_id)
        .first()
    )
    created = product is None
    if created:
        product = SkuProduct(platform=platform, sku_id=sku_id, product_name="")
        db.add(product)
        db.flush()

    product.product_name = _clean_text(payload.get("product_name")) or product.product_name or sku_id
    product.normalized_name = _clean_text(payload.get("normalized_name")) or product.product_name
    product.brand_name = _clean_text(payload.get("brand_name"))
    product.main_image_url = _clean_text(payload.get("main_image_url"))
    product.category_level_1 = _clean_text(payload.get("category_level_1"))
    product.category_level_2 = _clean_text(payload.get("category_level_2"))
    product.category_level_3 = _clean_text(payload.get("category_level_3"))
    product.category_id_3 = payload.get("category_id_3")
    product.shop_name = _clean_text(payload.get("shop_name"))
    product.product_url = _clean_text(payload.get("product_url"))
    product.status = int(payload.get("status", 1))
    db.flush()

    raw_attrs = payload.get("attributes") or []
    db.query(SkuProductAttr).filter(SkuProductAttr.sku_product_id == product.id).delete()
    normalized_attrs = [item for item in (_normalize_attr(attr) for attr in raw_attrs) if item]
    for attr in normalized_attrs:
        db.add(SkuProductAttr(sku_product_id=product.id, **attr))

    raw_tags = payload.get("tags") or []
    db.query(SkuTagRelation).filter(SkuTagRelation.sku_product_id == product.id).delete()
    tag_count = 0
    for raw_tag in raw_tags:
        tag = _ensure_tag_definition(db, raw_tag)
        if tag is None:
            continue
        db.add(
            SkuTagRelation(
                sku_product_id=product.id,
                tag_id=tag.id,
                source_type=_clean_text(raw_tag.get("source_type")) or "AUTO",
                tag_value=_clean_text(raw_tag.get("tag_value")),
            )
        )
        tag_count += 1

    raw_prices = payload.get("prices") or []
    if raw_prices:
        for raw_price in raw_prices:
            captured_at_str = raw_price.get("captured_at")
            try:
                captured_at = datetime.datetime.fromisoformat(captured_at_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

            # Check if snapshot already exists for this time
            existing = (
                db.query(SkuPriceSnapshot)
                .filter(
                    SkuPriceSnapshot.sku_product_id == product.id,
                    SkuPriceSnapshot.captured_at == captured_at,
                )
                .first()
            )
            if existing:
                existing.list_price = raw_price.get("list_price", 0)
                existing.reduction_amount = raw_price.get("reduction_amount", 0)
                existing.coupon_amount = raw_price.get("coupon_amount", 0)
                existing.other_discount_amount = raw_price.get("other_discount_amount", 0)
                existing.final_price = raw_price.get("final_price", 0)
                existing.promo_text = _clean_text(raw_price.get("promo_text"))
            else:
                db.add(
                    SkuPriceSnapshot(
                        sku_product_id=product.id,
                        captured_at=captured_at,
                        list_price=raw_price.get("list_price", 0),
                        reduction_amount=raw_price.get("reduction_amount", 0),
                        coupon_amount=raw_price.get("coupon_amount", 0),
                        other_discount_amount=raw_price.get("other_discount_amount", 0),
                        final_price=raw_price.get("final_price", 0),
                        promo_text=_clean_text(raw_price.get("promo_text")),
                    )
                )
        db.flush()

        # Update Extremum Points
        stats = (
            db.query(
                func.min(SkuPriceSnapshot.final_price).label("min_p"),
                func.max(SkuPriceSnapshot.final_price).label("max_p"),
                func.avg(SkuPriceSnapshot.final_price).label("avg_p"),
                func.count(SkuPriceSnapshot.id).label("cnt"),
            )
            .filter(SkuPriceSnapshot.sku_product_id == product.id)
            .first()
        )
        if stats and stats.cnt > 0:
            product.min_price = stats.min_p
            product.max_price = stats.max_p
            product.avg_price = int(stats.avg_p)
            product.snapshot_count = stats.cnt

    db.commit()
    db.refresh(product)

    return {
        "created": created,
        "platform": product.platform,
        "sku_id": product.sku_id,
        "product_id": product.id,
        "product_name": product.product_name,
        "attribute_count": len(normalized_attrs),
        "tag_count": tag_count,
    }
