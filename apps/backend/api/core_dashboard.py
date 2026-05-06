from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.session import get_db
from models import AnomalyAlert, CrawlEfficiency, SkuPriceSnapshot, SkuProduct
from schemas.sku import ApiResponse


router = APIRouter(prefix="/core-dashboard", tags=["core-dashboard"])


def dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    if hasattr(model, "dict"):
        return model.dict()
    return model


def ok(data, message: str = "ok"):
    return dump_model(ApiResponse(code=0, message=message, data=data))


def _format_bucket_time(value: datetime) -> str:
    return value.strftime("%H:%M")


def _floor_to_five_minutes(value: datetime) -> datetime:
    rounded = value.replace(second=0, microsecond=0)
    return rounded - timedelta(minutes=rounded.minute % 5)


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    now = datetime.now()
    current_bucket_start = _floor_to_five_minutes(now) - timedelta(minutes=5)
    current_bucket_end = current_bucket_start + timedelta(minutes=5)
    hour_ago = current_bucket_start - timedelta(minutes=55)

    total_sku_count = db.query(func.count(SkuProduct.id)).scalar() or 0
    total_price_records = db.query(func.count(SkuPriceSnapshot.id)).scalar() or 0
    pending_anomaly_count = (
        db.query(func.count(AnomalyAlert.id))
        .filter(AnomalyAlert.is_verified == 0)
        .scalar()
        or 0
    )

    platform_rows = (
        db.query(
            SkuProduct.platform.label("platform"),
            func.count(SkuProduct.id).label("sku_count"),
        )
        .group_by(SkuProduct.platform)
        .order_by(func.count(SkuProduct.id).desc(), SkuProduct.platform.asc())
        .all()
    )
    platform_breakdown = [
        {"platform": row.platform, "sku_count": int(row.sku_count or 0)}
        for row in platform_rows
    ]

    recent_efficiency = (
        db.query(CrawlEfficiency)
        .filter(CrawlEfficiency.captured_at >= hour_ago)
        .order_by(CrawlEfficiency.captured_at.asc())
        .all()
    )
    success_rate = 0.0
    if recent_efficiency:
        success_count = sum(1 for item in recent_efficiency if 200 <= item.status_code < 400)
        success_rate = round(success_count * 100 / len(recent_efficiency), 1)

    capture_timeline = []
    for index in range(12):
        bucket_start = hour_ago + timedelta(minutes=index * 5)
        bucket_end = bucket_start + timedelta(minutes=5)

        active_sku_count = (
        db.query(func.count(func.distinct(SkuPriceSnapshot.sku_product_id)))
        .filter(
            SkuPriceSnapshot.captured_at >= bucket_start,
            SkuPriceSnapshot.captured_at < bucket_end,
            SkuPriceSnapshot.is_anomalous == 0,
        )
        .scalar()
        or 0
        )

        bucket_efficiency = [
            item
            for item in recent_efficiency
            if bucket_start <= item.captured_at < bucket_end
        ]
        if bucket_efficiency:
            bucket_success = sum(
                1 for item in bucket_efficiency if 200 <= item.status_code < 400
            )
            bucket_success_rate = round(bucket_success * 100 / len(bucket_efficiency), 1)
        else:
            bucket_success_rate = success_rate

        capture_timeline.append(
            {
                "active_sku_count": int(active_sku_count),
                "success_rate": bucket_success_rate,
                "timestamp": _format_bucket_time(bucket_start),
            }
        )

    active_sku_count = (
        db.query(func.count(func.distinct(SkuPriceSnapshot.sku_product_id)))
        .filter(
            SkuPriceSnapshot.captured_at >= current_bucket_start,
            SkuPriceSnapshot.captured_at < current_bucket_end,
            SkuPriceSnapshot.is_anomalous == 0,
        )
        .scalar()
        or 0
    )

    latest_snapshots = (
        db.query(SkuPriceSnapshot)
        .join(SkuProduct, SkuProduct.id == SkuPriceSnapshot.sku_product_id)
        .filter(
            SkuPriceSnapshot.captured_at >= hour_ago,
            SkuPriceSnapshot.is_anomalous == 0,
        )
        .order_by(
            SkuPriceSnapshot.sku_product_id.asc(),
            SkuPriceSnapshot.captured_at.desc(),
        )
        .all()
    )

    snapshot_map: dict[int, list[SkuPriceSnapshot]] = {}
    for snapshot in latest_snapshots:
        history = snapshot_map.setdefault(snapshot.sku_product_id, [])
        if len(history) < 2:
            history.append(snapshot)

    alert_items = []
    for snapshots in snapshot_map.values():
        if len(snapshots) < 2:
            continue
        current, previous = snapshots[0], snapshots[1]
        if previous.final_price <= 0 or current.final_price >= previous.final_price:
            continue

        drop_percent = round(
            (previous.final_price - current.final_price) * 100 / previous.final_price,
            1,
        )
        if drop_percent <= 0:
            continue

        product = current.product
        alert_items.append(
            {
                "current_price": round(current.final_price / 100, 2),
                "detected_at": current.captured_at.strftime("%H:%M:%S"),
                "drop_percent": drop_percent,
                "platform": product.platform,
                "previous_price": round(previous.final_price / 100, 2),
                "product_name": product.normalized_name or product.product_name,
                "sku_id": product.sku_id,
            }
        )

    alert_items.sort(key=lambda item: item["drop_percent"], reverse=True)

    return ok(
        {
            "active_sku_count": active_sku_count,
            "alert_items": alert_items[:10],
            "capture_timeline": capture_timeline,
            "pending_anomaly_count": int(pending_anomaly_count),
            "platform_breakdown": platform_breakdown,
            "success_rate": success_rate,
            "total_price_records": int(total_price_records),
            "total_sku_count": int(total_sku_count),
        }
    )
