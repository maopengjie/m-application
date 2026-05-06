from __future__ import annotations

import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import AnomalyAlert, SkuPriceSnapshot, SkuProduct


VALID_PRICE_KEYWORDS = (
    "valid",
    "accept",
    "accepted",
    "real",
    "true price",
    "有效",
    "真实",
    "确认有效",
    "价格有效",
    "纳入",
)


def parse_alert_price_cents(alert_value: str | None) -> int | None:
    if not alert_value:
        return None
    match = re.search(r"\d+(?:\.\d+)?", alert_value.replace(",", ""))
    if not match:
        return None
    return int(round(float(match.group(0)) * 100))


def is_valid_price_verification(verification_result: str | None) -> bool:
    if not verification_result:
        return False
    normalized = verification_result.strip().lower()
    return any(keyword in normalized for keyword in VALID_PRICE_KEYWORDS)


def recompute_product_price_extremes(db: Session, product_id: int) -> dict[str, int | None]:
    product = db.query(SkuProduct).filter(SkuProduct.id == product_id).first()
    if product is None:
        return {
            "avg_price": None,
            "max_price": None,
            "min_price": None,
            "snapshot_count": 0,
        }

    stats = (
        db.query(
            func.min(SkuPriceSnapshot.final_price).label("min_price"),
            func.max(SkuPriceSnapshot.final_price).label("max_price"),
            func.avg(SkuPriceSnapshot.final_price).label("avg_price"),
            func.count(SkuPriceSnapshot.id).label("snapshot_count"),
        )
        .filter(
            SkuPriceSnapshot.sku_product_id == product_id,
            SkuPriceSnapshot.is_anomalous == 0,
        )
        .first()
    )

    count = int(stats.snapshot_count or 0) if stats else 0
    product.min_price = int(stats.min_price) if stats and stats.min_price is not None else None
    product.max_price = int(stats.max_price) if stats and stats.max_price is not None else None
    product.avg_price = int(stats.avg_price) if stats and stats.avg_price is not None else None
    product.snapshot_count = count

    return {
        "avg_price": product.avg_price,
        "max_price": product.max_price,
        "min_price": product.min_price,
        "snapshot_count": product.snapshot_count,
    }


def apply_anomaly_verification_to_snapshots(
    db: Session,
    anomaly: AnomalyAlert,
    verification_result: str | None,
) -> dict[str, int | None]:
    product = None
    if anomaly.product_id is not None:
        product = db.query(SkuProduct).filter(SkuProduct.id == anomaly.product_id).first()
    if product is None:
        product = (
            db.query(SkuProduct)
            .filter(
                SkuProduct.platform == anomaly.platform,
                SkuProduct.sku_id == anomaly.sku_id,
            )
            .first()
        )
    if product is None:
        return {
            "matched_snapshot_count": 0,
            "product_id": anomaly.product_id,
            "snapshot_count": 0,
            "unmarked_snapshot_count": 0,
        }

    alert_price = parse_alert_price_cents(anomaly.alert_value)
    snapshot_query = db.query(SkuPriceSnapshot).filter(
        SkuPriceSnapshot.sku_product_id == product.id,
        SkuPriceSnapshot.is_anomalous == 1,
    )
    if alert_price is not None:
        snapshot_query = snapshot_query.filter(SkuPriceSnapshot.final_price == alert_price)

    snapshots = snapshot_query.all()
    unmarked_count = 0
    if is_valid_price_verification(verification_result):
        for snapshot in snapshots:
            snapshot.is_anomalous = 0
            snapshot.anomaly_reason = None
            unmarked_count += 1

    stats = recompute_product_price_extremes(db, product.id)
    return {
        "matched_snapshot_count": len(snapshots),
        "product_id": product.id,
        "snapshot_count": stats["snapshot_count"],
        "unmarked_snapshot_count": unmarked_count,
    }
