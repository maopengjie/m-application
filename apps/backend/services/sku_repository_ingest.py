from __future__ import annotations

import re
import datetime
from typing import Any

from sqlalchemy.orm import Session

from models import SkuPriceSnapshot, SkuProduct, SkuProductAttr, SkuTagRelation, TagDefinition, EtlLog, AnomalyAlert, CrawlEfficiency
from services.mapping_service import apply_mapping_rules_to_product
from services.price_statistics import recompute_product_price_extremes


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


def _filter_ad_slogans(name: str) -> tuple[str, list[str]]:
    """
    Filters out advertising slogans from product names.
    Returns (cleaned_name, list_of_removed_slogans)
    """
    removed = []
    # Common JD/Tmall ad patterns
    patterns = [
        r"【.*?】",             # Brackets like 【4月狂欢】
        r"直播间专享",
        r"限时秒杀",
        r"领券立减\d*",
        r"满\d+减\d+",
        r"第[二三]件\d+折",
        r"拍\d+件.*?元",
        r"官方旗舰店",
        r"新品上市",
    ]
    
    cleaned = name
    for pattern in patterns:
        matches = re.findall(pattern, cleaned)
        if matches:
            removed.extend(matches)
            cleaned = re.sub(pattern, "", cleaned)
    
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned, removed


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


def _normalize_captured_at(raw_value: Any) -> datetime.datetime:
    if not raw_value or not isinstance(raw_value, str):
        raise ValueError("captured_at is required for each price snapshot")

    captured_at = datetime.datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    if captured_at.tzinfo is not None:
        captured_at = captured_at.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return captured_at


def _normalize_price_amount(raw_value: Any, field_name: str) -> int:
    try:
        value = int(raw_value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer amount in cents") from exc

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return value


def _classify_price_anomaly(final_price: int, list_price: int) -> str | None:
    if 0 < final_price < 100:
        return "PRICE_BELOW_1_RMB"
    if list_price > 0 and final_price > list_price:
        return "FINAL_PRICE_ABOVE_LIST_PRICE"
    return None


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

    original_name = _clean_text(payload.get("product_name")) or product.product_name or sku_id
    cleaned_name, removed_slogans = _filter_ad_slogans(original_name)
    
    product.product_name = cleaned_name
    
    if removed_slogans:
        db.add(EtlLog(
            event_type="CLEANING",
            platform=platform,
            sku_id=sku_id,
            product_id=product.id,
            field_name="product_name",
            original_value=original_name,
            cleaned_value=cleaned_name,
            message=f"Filtered slogans: {', '.join(removed_slogans)}"
        ))
    
    # Apply mapping rules if normalized_name is not explicitly provided in payload
    provided_normalized = _clean_text(payload.get("normalized_name"))
    if provided_normalized:
        product.normalized_name = provided_normalized
    else:
        apply_mapping_rules_to_product(db, product)
        
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
        now = datetime.datetime.utcnow()
        for raw_price in raw_prices:
            try:
                captured_at = _normalize_captured_at(raw_price.get("captured_at"))
            except ValueError as exc:
                raise ValueError(f"invalid captured_at for sku {sku_id}: {exc}") from exc

            if captured_at > now + datetime.timedelta(minutes=5):
                raise ValueError(f"captured_at cannot be in the future for sku {sku_id}")

            list_price = _normalize_price_amount(raw_price.get("list_price"), "list_price")
            reduction_amount = _normalize_price_amount(
                raw_price.get("reduction_amount"),
                "reduction_amount",
            )
            coupon_amount = _normalize_price_amount(
                raw_price.get("coupon_amount"),
                "coupon_amount",
            )
            other_discount_amount = _normalize_price_amount(
                raw_price.get("other_discount_amount"),
                "other_discount_amount",
            )
            final_price = _normalize_price_amount(raw_price.get("final_price"), "final_price")
            anomaly_reason = _clean_text(raw_price.get("anomaly_reason"))
            detected_anomaly = _classify_price_anomaly(final_price, list_price)
            is_anomalous = int(raw_price.get("is_anomalous") or 0)
            if detected_anomaly:
                is_anomalous = 1
                anomaly_reason = anomaly_reason or detected_anomaly

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
                existing.list_price = list_price
                existing.reduction_amount = reduction_amount
                existing.coupon_amount = coupon_amount
                existing.other_discount_amount = other_discount_amount
                existing.final_price = final_price
                existing.promo_text = _clean_text(raw_price.get("promo_text"))
                existing.is_anomalous = is_anomalous
                existing.anomaly_reason = anomaly_reason
            else:
                db.add(
                    SkuPriceSnapshot(
                        sku_product_id=product.id,
                        captured_at=captured_at,
                        list_price=list_price,
                        reduction_amount=reduction_amount,
                        coupon_amount=coupon_amount,
                        other_discount_amount=other_discount_amount,
                        final_price=final_price,
                        promo_text=_clean_text(raw_price.get("promo_text")),
                        is_anomalous=is_anomalous,
                        anomaly_reason=anomaly_reason,
                    )
                )
            
            # Anomaly Detection: Price < 1.00 RMB (100 cents)
            if is_anomalous:
                db.add(AnomalyAlert(
                    alert_type="PRICE_BUG",
                    platform=platform,
                    sku_id=sku_id,
                    product_id=product.id,
                    alert_value=f"{final_price/100:.2f}元",
                    threshold="valid final price",
                    message=f"Possible invalid price detected: {final_price/100:.2f} RMB ({anomaly_reason})"
                ))
        db.flush()

        # Pending anomaly snapshots are kept for audit, but excluded from
        # high/low/average analytics to avoid false low-price alerts.
        recompute_product_price_extremes(db, product.id)

    # Log Crawl Efficiency if provided
    efficiency = payload.get("efficiency")
    if efficiency:
        db.add(CrawlEfficiency(
            platform=platform,
            target_api=efficiency.get("target_api", "unknown"),
            response_time_ms=efficiency.get("response_time_ms", 0),
            status_code=efficiency.get("status_code", 200)
        ))

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
