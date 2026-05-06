from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import json
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from core.task_queue import enqueue_task
from db.session import get_db
from models import (
    CategoryNode,
    EtlLog,
    MappingRule,
    ScrapeTaskRun,
    SkuComparison,
    SkuPriceSnapshot,
    SkuProduct,
    SkuProductAttr,
    SkuTagRelation,
    TagDefinition,
)
from schemas.sku import (
    ApiResponse,
    CategoryImportNodeSchema,
    CategoryNodeSchema,
    CategoryTreeQuerySchema,
    CategoryTreeImportSchema,
    MappingRuleCreateUpdateSchema,
    MappingRuleQuerySchema,
    MappingRuleSchema,
    PriceExtremesSchema,
    PriceSnapshotSchema,
    PriceTimeSeriesDetailSchema,
    PriceTimeSeriesListDataSchema,
    PriceTimeSeriesListItemSchema,
    PriceTimeSeriesQuerySchema,
    PriceTimeSeriesSummarySchema,
    PromotionRecordSchema,
    ScrapeBatchRequestSchema,
    ScrapeProductRequestSchema,
    ScrapeTaskRunSchema,
    SkuComparisonQuerySchema,
    SkuComparisonReviewSchema,
    SkuComparisonSchema,
    SkuAttributeSchema,
    SkuImportPayloadSchema,
    SkuProductDetailSchema,
    SkuProductListDataSchema,
    SkuProductListItemSchema,
    SkuProductQuerySchema,
    SkuTagSchema,
    SkuTagUpsertSchema,
)
from services import ingest_sku_payload
from services.mapping_service import (
    apply_rules_to_all_products,
    auto_match_comparisons,
    explain_product_match,
)
from services.task_runs import mark_stale_scrape_runs


router = APIRouter(prefix="/sku-repository", tags=["sku-repository"])


def dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def ok(data, message: str = "ok"):
    return dump_model(ApiResponse(code=0, message=message, data=data))


def _audit(
    db: Session,
    *,
    action: str,
    operator: str | None,
    message: str,
    product_id: int | None = None,
    sku_id: str | None = None,
):
    db.add(
        EtlLog(
            event_type="AUDIT",
            product_id=product_id,
            sku_id=sku_id,
            field_name=action,
            original_value=operator or "Unknown",
            cleaned_value=message,
            message=f"{operator or 'Unknown'} {message}",
            status=1,
        )
    )


def _normalize_operator(operator: object | None) -> str | None:
    return operator if isinstance(operator, str) else None


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


def _get_or_create_manual_tag_definition(
    db: Session,
    tag_code: str,
    tag_name: str | None = None,
) -> TagDefinition:
    definition = db.query(TagDefinition).filter(TagDefinition.tag_code == tag_code).first()
    if definition is not None:
        if tag_name and definition.tag_name != tag_name:
            definition.tag_name = tag_name
        return definition

    definition = TagDefinition(
        tag_code=tag_code,
        tag_name=tag_name or tag_code,
        tag_type="MANUAL",
        description="Manual tag created from SKU repository",
    )
    db.add(definition)
    db.flush()
    return definition


def _price_to_yuan(value: int | None) -> float:
    return round((value or 0) / 100, 2)


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat(sep=" ", timespec="seconds")


def _serialize_scrape_task_run(run: ScrapeTaskRun) -> ScrapeTaskRunSchema:
    failed_items: list[dict[str, object]] = []
    if run.failed_items_json:
        try:
            parsed = json.loads(run.failed_items_json)
            if isinstance(parsed, list):
                failed_items = parsed
        except json.JSONDecodeError:
            failed_items = []

    return ScrapeTaskRunSchema(
        id=run.id,
        task_id=run.task_id,
        task_name=run.task_name,
        trigger_source=run.trigger_source,
        platform=run.platform,
        requested_limit=run.requested_limit,
        requested_url=run.requested_url,
        status=run.status,
        processed_count=run.processed_count,
        success_count=run.success_count,
        failure_count=run.failure_count,
        started_at=_format_datetime(run.started_at),
        finished_at=_format_datetime(run.finished_at),
        summary_message=run.summary_message,
        error_message=run.error_message,
        failed_items=failed_items,
        created_at=_format_datetime(run.created_at) or "",
        updated_at=_format_datetime(run.updated_at) or "",
    )


def _build_price_formula(snapshot: SkuPriceSnapshot) -> str:
    segments = [
        snapshot.captured_at.isoformat(sep=" ", timespec="seconds"),
        f"标价 {_price_to_yuan(snapshot.list_price):.2f}",
    ]
    if snapshot.reduction_amount:
        segments.append(f"满减 -{_price_to_yuan(snapshot.reduction_amount):.2f}")
    if snapshot.coupon_amount:
        segments.append(f"券 -{_price_to_yuan(snapshot.coupon_amount):.2f}")
    if snapshot.other_discount_amount:
        segments.append(f"补贴 -{_price_to_yuan(snapshot.other_discount_amount):.2f}")
    segments.append(f"到手 {_price_to_yuan(snapshot.final_price):.2f}")
    return ", ".join(segments)


def _serialize_price_snapshot(snapshot: SkuPriceSnapshot, min_final_price: int) -> PriceSnapshotSchema:
    return PriceSnapshotSchema(
        anomaly_reason=snapshot.anomaly_reason,
        captured_at=snapshot.captured_at.isoformat(sep=" ", timespec="seconds"),
        final_price=_price_to_yuan(snapshot.final_price),
        is_anomalous=bool(snapshot.is_anomalous),
        is_historical_low=snapshot.is_anomalous == 0 and snapshot.final_price == min_final_price,
        list_price=_price_to_yuan(snapshot.list_price),
        promo_text=snapshot.promo_text,
    )


def _build_price_list_item(product: SkuProduct, latest_snapshot: SkuPriceSnapshot | None) -> PriceTimeSeriesListItemSchema:
    return PriceTimeSeriesListItemSchema(
        average_price=_price_to_yuan(product.avg_price),
        brand_name=product.brand_name,
        capture_count=product.snapshot_count,
        current_price=_price_to_yuan(latest_snapshot.final_price) if latest_snapshot else 0,
        highest_price=_price_to_yuan(product.max_price),
        id=product.id,
        latest_capture_at=latest_snapshot.captured_at.isoformat(sep=" ", timespec="seconds") if latest_snapshot else product.updated_at.isoformat(sep=" ", timespec="seconds"),
        lowest_price=_price_to_yuan(product.min_price),
        main_image_url=product.main_image_url,
        platform=product.platform,
        product_name=product.normalized_name or product.product_name,
        recent_promo_text=latest_snapshot.promo_text if latest_snapshot else None,
        shop_name=product.shop_name,
        sku_id=product.sku_id,
        status=product.status,
    )


def _has_active_promotion(snapshot: SkuPriceSnapshot | None) -> bool:
    if snapshot is None:
        return False
    return bool(
        snapshot.promo_text
        or snapshot.reduction_amount > 0
        or snapshot.coupon_amount > 0
        or snapshot.other_discount_amount > 0
    )


def _refresh_mapping_outputs(db: Session) -> dict[str, int]:
    updated_count = apply_rules_to_all_products(db)
    matched_count = auto_match_comparisons(db)
    return {
        "matched_count": matched_count,
        "updated_count": updated_count,
    }


def _is_enabled(value: str | None) -> bool:
    return (value or "").lower() in {"1", "true", "yes"}


@router.get("/products")
def list_products(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    brand_name: str | None = None,
    platform: str | None = None,
    tag_code: str | None = None,
    category_id: int | None = None,
    category_level: int | None = None,
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
    
    if query_params.category_id:
        # If we have a category_id, we need to know what level it is
        cat_node = db.query(CategoryNode).filter(CategoryNode.id == query_params.category_id).first()
        if cat_node:
            if cat_node.level == 1:
                query = query.filter(SkuProduct.category_level_1 == cat_node.name)
            elif cat_node.level == 2:
                query = query.filter(SkuProduct.category_level_2 == cat_node.name)
            elif cat_node.level == 3:
                # Use platform category ID if available, otherwise name
                if cat_node.external_id and cat_node.external_id.isdigit():
                    query = query.filter(SkuProduct.category_id_3 == int(cat_node.external_id))
                else:
                    query = query.filter(SkuProduct.category_level_3 == cat_node.name)

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


@router.post("/products/{product_id}/tags")
def add_product_tag(
    product_id: int,
    payload: SkuTagUpsertSchema,
    x_operator: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    product = db.query(SkuProduct).filter(SkuProduct.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="SKU product not found")

    tag_code = payload.tag_code.strip()
    if not tag_code:
        raise HTTPException(status_code=400, detail="tag_code is required")

    definition = _get_or_create_manual_tag_definition(
        db,
        tag_code=tag_code,
        tag_name=payload.tag_name.strip() if payload.tag_name else None,
    )
    relation = (
        db.query(SkuTagRelation)
        .filter(
            SkuTagRelation.sku_product_id == product_id,
            SkuTagRelation.tag_id == definition.id,
        )
        .first()
    )
    if relation is None:
        relation = SkuTagRelation(
            sku_product_id=product_id,
            tag_id=definition.id,
            source_type="MANUAL",
            tag_value=payload.tag_value.strip() if payload.tag_value else None,
        )
        db.add(relation)
    else:
        relation.source_type = "MANUAL"
        relation.tag_value = payload.tag_value.strip() if payload.tag_value else None

    _audit(
        db,
        action="TAG_ADD",
        operator=_normalize_operator(x_operator),
        product_id=product_id,
        sku_id=product.sku_id,
        message=f"添加/更新标签 {tag_code}",
    )
    db.commit()
    updated_tags = _build_tag_map(db, [product_id]).get(product_id, [])
    return ok(
        [dump_model(item) for item in updated_tags],
        message="SKU 标签已更新",
    )


@router.delete("/products/{product_id}/tags/{tag_id}")
def delete_product_tag(
    product_id: int,
    tag_id: int,
    x_operator: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    product = db.query(SkuProduct).filter(SkuProduct.id == product_id).first()
    tag = db.query(TagDefinition).filter(TagDefinition.id == tag_id).first()
    relation = (
        db.query(SkuTagRelation)
        .filter(
            SkuTagRelation.sku_product_id == product_id,
            SkuTagRelation.tag_id == tag_id,
        )
        .first()
    )
    if relation is None:
        raise HTTPException(status_code=404, detail="SKU tag relation not found")

    _audit(
        db,
        action="TAG_DELETE",
        operator=_normalize_operator(x_operator),
        product_id=product_id,
        sku_id=product.sku_id if product else None,
        message=f"删除标签 {tag.tag_code if tag else tag_id}",
    )
    db.delete(relation)
    db.commit()
    updated_tags = _build_tag_map(db, [product_id]).get(product_id, [])
    return ok(
        [dump_model(item) for item in updated_tags],
        message="SKU 标签已删除",
    )


@router.get("/price-time-series")
def list_price_time_series(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    platform: str | None = None,
    status: int | None = None,
    db: Session = Depends(get_db),
):
    query_params = PriceTimeSeriesQuerySchema(
        page=page,
        page_size=page_size,
        keyword=keyword,
        platform=platform,
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
    if query_params.platform:
        query = query.filter(SkuProduct.platform == query_params.platform.strip())
    if query_params.status is not None:
        query = query.filter(SkuProduct.status == query_params.status)

    filtered_product_ids = query.with_entities(SkuProduct.id).subquery()
    filtered_product_id_select = select(filtered_product_ids.c.id)
    total = query.count()
    products = (
        query.order_by(SkuProduct.updated_at.desc(), SkuProduct.id.desc())
        .offset((query_params.page - 1) * query_params.page_size)
        .limit(query_params.page_size)
        .all()
    )

    product_ids = [item.id for item in products]
    
    # Get latest snapshot for each product to show current price/promo
    latest_snapshots = (
        db.query(SkuPriceSnapshot)
        .filter(
            SkuPriceSnapshot.sku_product_id.in_(product_ids),
            SkuPriceSnapshot.is_anomalous == 0,
        )
        .order_by(SkuPriceSnapshot.captured_at.desc())
        .all()
    )
    latest_map: dict[int, SkuPriceSnapshot] = {}
    for snapshot in latest_snapshots:
        if snapshot.sku_product_id not in latest_map:
            latest_map[snapshot.sku_product_id] = snapshot

    items = [_build_price_list_item(product, latest_map.get(product.id)) for product in products]

    total_sku_count = (
        db.query(func.count(SkuProduct.id))
        .filter(SkuProduct.id.in_(filtered_product_id_select))
        .scalar()
        or 0
    )
    total_snapshots = (
        db.query(func.count(SkuPriceSnapshot.id))
        .filter(
            SkuPriceSnapshot.sku_product_id.in_(filtered_product_id_select),
            SkuPriceSnapshot.is_anomalous == 0,
        )
        .scalar()
        or 0
    )

    latest_capture_subquery = (
        db.query(
            SkuPriceSnapshot.sku_product_id.label("sku_product_id"),
            func.max(SkuPriceSnapshot.captured_at).label("latest_captured_at"),
        )
        .filter(
            SkuPriceSnapshot.sku_product_id.in_(filtered_product_id_select),
            SkuPriceSnapshot.is_anomalous == 0,
        )
        .group_by(SkuPriceSnapshot.sku_product_id)
        .subquery()
    )

    latest_summary_rows = (
        db.query(SkuProduct, SkuPriceSnapshot)
        .outerjoin(
            latest_capture_subquery,
            SkuProduct.id == latest_capture_subquery.c.sku_product_id,
        )
        .outerjoin(
            SkuPriceSnapshot,
            and_(
                SkuPriceSnapshot.sku_product_id == latest_capture_subquery.c.sku_product_id,
                SkuPriceSnapshot.captured_at == latest_capture_subquery.c.latest_captured_at,
            ),
        )
        .filter(SkuProduct.id.in_(filtered_product_id_select))
        .all()
    )

    latest_discount_rates = []
    active_promotion_count = 0
    lowest_price_sku_count = 0
    for product, latest_snapshot in latest_summary_rows:
        if latest_snapshot is None:
            continue
        if _has_active_promotion(latest_snapshot):
            active_promotion_count += 1
        if product.min_price is not None and latest_snapshot.final_price == product.min_price:
            lowest_price_sku_count += 1
        if latest_snapshot.list_price and latest_snapshot.list_price > 0:
            latest_discount_rates.append(
                (latest_snapshot.list_price - latest_snapshot.final_price)
                * 100.0
                / latest_snapshot.list_price
            )

    avg_discount_rate = round(
        sum(latest_discount_rates) / len(latest_discount_rates),
        1,
    ) if latest_discount_rates else 0

    summary = PriceTimeSeriesSummarySchema(
        active_promotion_count=active_promotion_count,
        avg_discount_rate=avg_discount_rate,
        lowest_price_sku_count=lowest_price_sku_count,
        total_sku_count=total_sku_count,
        total_snapshot_count=total_snapshots,
    )
    payload = PriceTimeSeriesListDataSchema(
        items=items,
        page=query_params.page,
        page_size=query_params.page_size,
        summary=summary,
        total=total,
    )
    return ok(dump_model(payload))


@router.get("/price-time-series/{product_id}")
def get_price_time_series_detail(product_id: int, db: Session = Depends(get_db)):
    product = db.query(SkuProduct).filter(SkuProduct.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="SKU product not found")

    snapshots = (
        db.query(SkuPriceSnapshot)
        .filter(SkuPriceSnapshot.sku_product_id == product_id)
        .order_by(SkuPriceSnapshot.captured_at.asc())
        .all()
    )
    if not snapshots:
        payload = PriceTimeSeriesDetailSchema(
            price_extremes=PriceExtremesSchema(
                average_price=_price_to_yuan(product.avg_price),
                current_price=0,
                highest_price=_price_to_yuan(product.max_price),
                highest_price_at=None,
                lowest_price=_price_to_yuan(product.min_price),
                lowest_price_at=None,
                price_span=_price_to_yuan((product.max_price or 0) - (product.min_price or 0)),
            ),
            product=_build_price_list_item(product, None),
            promotion_records=[],
            timeline=[],
        )
        return ok(dump_model(payload))

    valid_snapshots = [item for item in snapshots if item.is_anomalous == 0]
    if not valid_snapshots:
        payload = PriceTimeSeriesDetailSchema(
            price_extremes=PriceExtremesSchema(
                average_price=0,
                current_price=0,
                highest_price=0,
                highest_price_at=None,
                lowest_price=0,
                lowest_price_at=None,
                price_span=0,
            ),
            product=_build_price_list_item(product, None),
            promotion_records=[],
            timeline=[
                _serialize_price_snapshot(snapshot, 0)
                for snapshot in snapshots
            ],
        )
        return ok(dump_model(payload))

    final_prices = [item.final_price for item in valid_snapshots]
    min_final_price = min(final_prices)
    lowest = min(valid_snapshots, key=lambda item: item.final_price)
    highest = max(valid_snapshots, key=lambda item: item.final_price)
    latest = valid_snapshots[-1]

    payload = PriceTimeSeriesDetailSchema(
        price_extremes=PriceExtremesSchema(
            average_price=_price_to_yuan(product.avg_price),
            current_price=_price_to_yuan(latest.final_price),
            highest_price=_price_to_yuan(product.max_price),
            highest_price_at=highest.captured_at.isoformat(sep=" ", timespec="seconds"),
            lowest_price=_price_to_yuan(product.min_price),
            lowest_price_at=lowest.captured_at.isoformat(sep=" ", timespec="seconds"),
            price_span=_price_to_yuan(product.max_price - product.min_price) if product.max_price and product.min_price else 0,
        ),
        product=_build_price_list_item(product, latest),
        promotion_records=[
            PromotionRecordSchema(
                captured_at=snapshot.captured_at.isoformat(sep=" ", timespec="seconds"),
                coupon_amount=_price_to_yuan(snapshot.coupon_amount),
                final_price=_price_to_yuan(snapshot.final_price),
                formula=_build_price_formula(snapshot),
                list_price=_price_to_yuan(snapshot.list_price),
                other_discount_amount=_price_to_yuan(snapshot.other_discount_amount),
                promo_text=snapshot.promo_text,
                reduction_amount=_price_to_yuan(snapshot.reduction_amount),
            )
            for snapshot in reversed(snapshots)
            if snapshot.is_anomalous == 0
            and (snapshot.reduction_amount or snapshot.coupon_amount or snapshot.other_discount_amount)
        ],
        timeline=[
            _serialize_price_snapshot(snapshot, min_final_price)
            for snapshot in snapshots
        ],
    )
    return ok(dump_model(payload))


@router.post("/imports/payload")
def import_product_payload(payload: SkuImportPayloadSchema, db: Session = Depends(get_db)):
    result = ingest_sku_payload(db, dump_model(payload))
    return ok(result, message="SKU import completed")


@router.post("/scraping/trigger")
def trigger_scrape_product(
    payload: ScrapeProductRequestSchema,
    x_operator: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    run = ScrapeTaskRun(
        task_name="scrape_product",
        trigger_source="MANUAL",
        requested_url=payload.url,
        status="PENDING",
        summary_message="等待 worker 抓取商品详情",
    )
    db.add(run)
    db.flush()

    try:
        task_id = enqueue_task("tasks.scraping.scrape_product", payload.url, run.id)
        run.task_id = task_id
        _audit(
            db,
            action="SCRAPE_PRODUCT_TRIGGER",
            operator=_normalize_operator(x_operator),
            message=f"触发单商品抓取 run #{run.id}",
        )
        db.commit()
        db.refresh(run)
    except Exception as exc:
        run.status = "FAILED"
        run.summary_message = "任务投递失败"
        run.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=503, detail="Scrape worker is unavailable") from exc

    return ok(
        {
            "run": dump_model(_serialize_scrape_task_run(run)),
            "task_id": task_id,
            "url": payload.url,
        },
        message="商品抓取任务已投递",
    )


@router.post("/scraping/batch")
def trigger_batch_scrape(
    payload: ScrapeBatchRequestSchema,
    x_operator: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    run = ScrapeTaskRun(
        task_name="scrape_active_products",
        trigger_source="MANUAL",
        platform=payload.platform,
        requested_limit=payload.limit,
        status="PENDING",
        summary_message="等待 worker 批量抓取在售商品",
    )
    db.add(run)
    db.flush()

    try:
        task_id = enqueue_task(
            "tasks.scraping.scrape_active_products",
            payload.limit,
            payload.platform,
            run.id,
        )
        run.task_id = task_id
        _audit(
            db,
            action="SCRAPE_BATCH_TRIGGER",
            operator=_normalize_operator(x_operator),
            message=f"触发批量抓取 run #{run.id}，平台 {payload.platform or '全部'}，上限 {payload.limit}",
        )
        db.commit()
        db.refresh(run)
    except Exception as exc:
        run.status = "FAILED"
        run.summary_message = "任务投递失败"
        run.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=503, detail="Scrape worker is unavailable") from exc

    return ok(
        {
            "limit": payload.limit,
            "platform": payload.platform,
            "run": dump_model(_serialize_scrape_task_run(run)),
            "task_id": task_id,
        },
        message="批量重抓任务已投递",
    )


@router.get("/scraping/runs")
def list_scrape_runs(
    limit: int = 10,
    status: str | None = None,
    platform: str | None = None,
    db: Session = Depends(get_db),
):
    if mark_stale_scrape_runs(db):
        db.commit()

    safe_limit = min(max(limit, 1), 50)
    query = db.query(ScrapeTaskRun)
    if status:
        query = query.filter(ScrapeTaskRun.status == status.strip())
    if platform:
        query = query.filter(ScrapeTaskRun.platform == platform.strip())

    runs = (
        query.order_by(ScrapeTaskRun.created_at.desc(), ScrapeTaskRun.id.desc())
        .limit(safe_limit)
        .all()
    )
    return ok([dump_model(_serialize_scrape_task_run(run)) for run in runs])


@router.get("/scraping/overview")
def get_scrape_overview(db: Session = Depends(get_db)):
    if mark_stale_scrape_runs(db):
        db.commit()

    status_rows = (
        db.query(ScrapeTaskRun.status, func.count(ScrapeTaskRun.id))
        .group_by(ScrapeTaskRun.status)
        .all()
    )
    status_counts = {status: int(count or 0) for status, count in status_rows}
    terminal_statuses = ["SUCCESS", "PARTIAL_SUCCESS", "FAILED", "TIMEOUT"]
    open_statuses = ["PENDING", "RUNNING"]

    latest_run = (
        db.query(ScrapeTaskRun)
        .order_by(ScrapeTaskRun.created_at.desc(), ScrapeTaskRun.id.desc())
        .first()
    )
    latest_success = (
        db.query(ScrapeTaskRun)
        .filter(ScrapeTaskRun.status == "SUCCESS")
        .order_by(ScrapeTaskRun.finished_at.desc().nullslast(), ScrapeTaskRun.id.desc())
        .first()
    )
    latest_problem = (
        db.query(ScrapeTaskRun)
        .filter(ScrapeTaskRun.status.in_(["FAILED", "PARTIAL_SUCCESS", "TIMEOUT"]))
        .order_by(ScrapeTaskRun.updated_at.desc(), ScrapeTaskRun.id.desc())
        .first()
    )

    total_runs = sum(status_counts.values())
    success_count = status_counts.get("SUCCESS", 0)
    terminal_count = sum(status_counts.get(status, 0) for status in terminal_statuses)
    success_rate = round(success_count * 100 / terminal_count, 1) if terminal_count else 0

    return ok(
        {
            "latest_problem_run": dump_model(_serialize_scrape_task_run(latest_problem)) if latest_problem else None,
            "latest_run": dump_model(_serialize_scrape_task_run(latest_run)) if latest_run else None,
            "latest_success_run": dump_model(_serialize_scrape_task_run(latest_success)) if latest_success else None,
            "open_run_count": sum(status_counts.get(status, 0) for status in open_statuses),
            "schedule": {
                "category_sync_enabled": _is_enabled(os.getenv("ENABLE_PERIODIC_CATEGORY_SYNC")),
                "category_sync_hours": int(os.getenv("PERIODIC_CATEGORY_SYNC_HOURS", "24")),
                "maintenance_interval_minutes": int(os.getenv("MAINTENANCE_INTERVAL_MINUTES", "5")),
                "periodic_scrape_enabled": _is_enabled(os.getenv("ENABLE_PERIODIC_SCRAPE")),
                "periodic_scrape_interval_minutes": int(os.getenv("PERIODIC_SCRAPE_INTERVAL_MINUTES", "30")),
                "periodic_scrape_limit": int(os.getenv("PERIODIC_SCRAPE_LIMIT", "20")),
                "periodic_scrape_platform": os.getenv("PERIODIC_SCRAPE_PLATFORM") or None,
            },
            "status_counts": status_counts,
            "success_rate": success_rate,
            "total_runs": total_runs,
        }
    )


@router.get("/scraping/runs/{run_id}")
def get_scrape_run_detail(run_id: int, db: Session = Depends(get_db)):
    if mark_stale_scrape_runs(db):
        db.commit()

    run = db.query(ScrapeTaskRun).filter(ScrapeTaskRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="Scrape task run not found")
    return ok(dump_model(_serialize_scrape_task_run(run)))


@router.post("/scraping/runs/{run_id}/retry")
def retry_scrape_run(
    run_id: int,
    x_operator: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if mark_stale_scrape_runs(db):
        db.commit()

    previous_run = db.query(ScrapeTaskRun).filter(ScrapeTaskRun.id == run_id).first()
    if previous_run is None:
        raise HTTPException(status_code=404, detail="Scrape task run not found")
    if previous_run.task_name not in {"scrape_product", "scrape_active_products", "sync_jd_category_tree"}:
        raise HTTPException(status_code=400, detail="This task type cannot be retried")

    retry_run = ScrapeTaskRun(
        task_name=previous_run.task_name,
        trigger_source="MANUAL_RETRY",
        platform=previous_run.platform,
        requested_limit=previous_run.requested_limit,
        requested_url=previous_run.requested_url,
        status="PENDING",
        summary_message=f"重试任务，来源 run #{previous_run.id}",
    )
    db.add(retry_run)
    db.flush()

    try:
        if previous_run.task_name == "scrape_product":
            if not previous_run.requested_url:
                raise ValueError("previous run has no requested_url")
            task_id = enqueue_task(
                "tasks.scraping.scrape_product",
                previous_run.requested_url,
                retry_run.id,
            )
        elif previous_run.task_name == "scrape_active_products":
            task_id = enqueue_task(
                "tasks.scraping.scrape_active_products",
                previous_run.requested_limit or 20,
                previous_run.platform,
                retry_run.id,
            )
        else:
            task_id = enqueue_task("tasks.scraping.sync_jd_category_tree", retry_run.id)
        retry_run.task_id = task_id
        _audit(
            db,
            action="SCRAPE_RETRY",
            operator=_normalize_operator(x_operator),
            message=f"重试抓取任务 #{previous_run.id}，新任务 #{retry_run.id}",
        )
        db.commit()
        db.refresh(retry_run)
    except Exception as exc:
        retry_run.status = "FAILED"
        retry_run.summary_message = "重试任务投递失败"
        retry_run.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=503, detail="Scrape worker is unavailable") from exc

    return ok(
        {
            "previous_run_id": previous_run.id,
            "run": dump_model(_serialize_scrape_task_run(retry_run)),
            "task_id": retry_run.task_id,
        },
        message="重试任务已投递",
    )


@router.get("/category-tree")
def get_category_tree(platform: str = "jd", db: Session = Depends(get_db)):
    # Check if we need to seed some demo categories
    if db.query(CategoryNode).filter(CategoryNode.platform == platform).count() == 0:
        _seed_demo_categories(db, platform)

    nodes = db.query(CategoryNode).filter(CategoryNode.platform == platform).order_by(CategoryNode.sort_order.asc()).all()
    
    # Build tree
    node_map = {}
    root_nodes = []
    
    for node in nodes:
        schema = CategoryNodeSchema(
            id=node.id,
            platform=node.platform,
            external_id=node.external_id,
            name=node.name,
            level=node.level,
            parent_id=node.parent_id,
            path=node.path,
            sort_order=node.sort_order,
            children=[]
        )
        node_map[node.id] = schema
        if node.level == 1:
            root_nodes.append(schema)
            
    for node in nodes:
        if node.parent_id and node.parent_id in node_map:
            node_map[node.parent_id].children.append(node_map[node.id])
            
    return ok([dump_model(n) for n in root_nodes])


def _insert_category_import_nodes(
    db: Session,
    *,
    nodes: list[CategoryImportNodeSchema],
    platform: str,
    level: int,
    parent_id: int | None,
    parent_path: str,
) -> int:
    imported_count = 0
    for index, item in enumerate(nodes):
        if level > 3:
            continue

        node = CategoryNode(
            platform=platform,
            external_id=item.external_id,
            name=item.name.strip(),
            level=level,
            parent_id=parent_id,
            sort_order=item.sort_order if item.sort_order is not None else index,
        )
        db.add(node)
        db.flush()

        node.path = f"{parent_path}/{node.id}" if parent_path else str(node.id)
        imported_count += 1
        imported_count += _insert_category_import_nodes(
            db,
            nodes=item.children,
            platform=platform,
            level=level + 1,
            parent_id=node.id,
            parent_path=node.path,
        )
    return imported_count


@router.post("/category-tree/import")
def import_category_tree(payload: CategoryTreeImportSchema, db: Session = Depends(get_db)):
    platform = payload.platform.strip() or "jd"
    if not payload.nodes:
        raise HTTPException(status_code=400, detail="nodes cannot be empty")

    db.query(CategoryNode).filter(CategoryNode.platform == platform).delete()
    imported_count = _insert_category_import_nodes(
        db,
        nodes=payload.nodes,
        platform=platform,
        level=1,
        parent_id=None,
        parent_path="",
    )
    db.commit()
    return ok(
        {
            "imported_count": imported_count,
            "platform": platform,
        },
        message=f"已导入 {imported_count} 个类目节点",
    )


@router.post("/category-tree/sync")
def trigger_category_tree_sync(db: Session = Depends(get_db)):
    run = ScrapeTaskRun(
        task_name="sync_jd_category_tree",
        trigger_source="MANUAL",
        platform="jd",
        requested_url="https://www.jd.com/allSort.aspx",
        status="PENDING",
        summary_message="等待 worker 同步京东类目树",
    )
    db.add(run)
    db.flush()

    try:
        task_id = enqueue_task("tasks.scraping.sync_jd_category_tree", run.id)
        run.task_id = task_id
        db.commit()
        db.refresh(run)
    except Exception as exc:
        run.status = "FAILED"
        run.summary_message = "任务投递失败"
        run.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=503, detail="Scrape worker is unavailable") from exc

    return ok(
        {
            "run": dump_model(_serialize_scrape_task_run(run)),
            "task_id": task_id,
        },
        message="京东类目同步任务已投递",
    )


@router.get("/mapping-rules")
def list_mapping_rules(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    platform: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(MappingRule)
    if keyword:
        query = query.filter(
            or_(
                MappingRule.pattern.ilike(f"%{keyword}%"),
                MappingRule.unified_label.ilike(f"%{keyword}%")
            )
        )
    if platform:
        query = query.filter(
            or_(
                MappingRule.platform == platform,
                MappingRule.platform.is_(None),
            )
        )
    
    total = query.count()
    active_total = query.filter(MappingRule.is_active == 1).count()
    rules = query.order_by(MappingRule.priority.desc(), MappingRule.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    items = [
        MappingRuleSchema(
            id=r.id,
            rule_type=r.rule_type,
            platform=r.platform,
            category_id=r.category_id,
            pattern=r.pattern,
            unified_label=r.unified_label,
            is_active=r.is_active,
            priority=r.priority,
            created_at=r.created_at.isoformat(sep=" ", timespec="seconds"),
            updated_at=r.updated_at.isoformat(sep=" ", timespec="seconds")
        )
        for r in rules
    ]
    
    return ok({"items": [dump_model(i) for i in items], "total": total, "active_total": active_total})


@router.post("/mapping-rules")
def create_mapping_rule(rule: MappingRuleCreateUpdateSchema, db: Session = Depends(get_db)):
    db_rule = MappingRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    refresh_result = _refresh_mapping_outputs(db) if db_rule.is_active else {"matched_count": 0, "updated_count": 0}
    return ok(
        {
            "rule": dump_model(
                MappingRuleSchema(
                    id=db_rule.id,
                    rule_type=db_rule.rule_type,
                    platform=db_rule.platform,
                    category_id=db_rule.category_id,
                    pattern=db_rule.pattern,
                    unified_label=db_rule.unified_label,
                    is_active=db_rule.is_active,
                    priority=db_rule.priority,
                    created_at=db_rule.created_at.isoformat(sep=" ", timespec="seconds"),
                    updated_at=db_rule.updated_at.isoformat(sep=" ", timespec="seconds"),
                )
            ),
            **refresh_result,
        },
        message="映射规则已创建并刷新归一化结果",
    )


@router.put("/mapping-rules/{rule_id}")
def update_mapping_rule(
    rule_id: int,
    payload: MappingRuleCreateUpdateSchema,
    db: Session = Depends(get_db),
):
    rule = db.query(MappingRule).filter(MappingRule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Mapping rule not found")

    for key, value in payload.model_dump().items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    refresh_result = _refresh_mapping_outputs(db)
    return ok(
        {
            "rule": dump_model(
                MappingRuleSchema(
                    id=rule.id,
                    rule_type=rule.rule_type,
                    platform=rule.platform,
                    category_id=rule.category_id,
                    pattern=rule.pattern,
                    unified_label=rule.unified_label,
                    is_active=rule.is_active,
                    priority=rule.priority,
                    created_at=rule.created_at.isoformat(sep=" ", timespec="seconds"),
                    updated_at=rule.updated_at.isoformat(sep=" ", timespec="seconds"),
                )
            ),
            **refresh_result,
        },
        message="映射规则已更新并刷新归一化结果",
    )


@router.patch("/mapping-rules/{rule_id}/status")
def toggle_mapping_rule_status(
    rule_id: int,
    is_active: int,
    db: Session = Depends(get_db),
):
    rule = db.query(MappingRule).filter(MappingRule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Mapping rule not found")

    rule.is_active = 1 if is_active else 0
    db.commit()
    db.refresh(rule)
    refresh_result = _refresh_mapping_outputs(db)
    return ok(
        {
            "rule": dump_model(
                MappingRuleSchema(
                    id=rule.id,
                    rule_type=rule.rule_type,
                    platform=rule.platform,
                    category_id=rule.category_id,
                    pattern=rule.pattern,
                    unified_label=rule.unified_label,
                    is_active=rule.is_active,
                    priority=rule.priority,
                    created_at=rule.created_at.isoformat(sep=" ", timespec="seconds"),
                    updated_at=rule.updated_at.isoformat(sep=" ", timespec="seconds"),
                )
            ),
            **refresh_result,
        },
        message="映射规则状态已更新并刷新归一化结果",
    )


@router.delete("/mapping-rules/{rule_id}")
def delete_mapping_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(MappingRule).filter(MappingRule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Mapping rule not found")

    db.delete(rule)
    db.commit()
    return ok({"deleted_id": rule_id}, message="映射规则已删除")


@router.post("/mapping-rules/apply")
def batch_apply_rules(db: Session = Depends(get_db)):
    count = apply_rules_to_all_products(db)
    return ok({"updated_count": count}, message=f"Successfully applied rules to {count} products")


@router.get("/sku-comparisons")
def list_sku_comparisons(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(SkuComparison).filter(SkuComparison.status >= 0)
    total = query.count()
    comparisons = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Enrich with SKU data
    sku_ids = set()
    for c in comparisons:
        sku_ids.add(c.master_sku_id)
        sku_ids.add(c.linked_sku_id)
        
    skus = db.query(SkuProduct).filter(SkuProduct.id.in_(list(sku_ids))).all()
    sku_map = {s.id: s for s in skus}
    attrs = (
        db.query(SkuProductAttr)
        .filter(SkuProductAttr.sku_product_id.in_(list(sku_ids)))
        .all()
    )
    attr_map: dict[int, list[SkuProductAttr]] = {}
    for attr in attrs:
        attr_map.setdefault(attr.sku_product_id, []).append(attr)
    
    items = []
    for c in comparisons:
        master = sku_map.get(c.master_sku_id)
        linked = sku_map.get(c.linked_sku_id)
        reasons: list[str] = []
        if master and linked:
            _, reasons = explain_product_match(
                master,
                linked,
                attr_map.get(master.id, []),
                attr_map.get(linked.id, []),
            )
        
        items.append(SkuComparisonSchema(
            id=c.id,
            master_sku_id=c.master_sku_id,
            linked_sku_id=c.linked_sku_id,
            match_score=c.match_score,
            match_reasons=reasons,
            match_type=c.match_type,
            status=c.status,
            master_sku=_serialize_sku_basic(master) if master else None,
            linked_sku=_serialize_sku_basic(linked) if linked else None
        ))
        
    return ok({"items": [dump_model(i) for i in items], "total": total})


@router.post("/sku-comparisons/auto-match")
def trigger_auto_match(db: Session = Depends(get_db)):
    count = auto_match_comparisons(db)
    return ok({"matched_count": count}, message=f"Successfully matched {count} products across platforms")


@router.patch("/sku-comparisons/{comparison_id}/review")
def review_sku_comparison(
    comparison_id: int,
    payload: SkuComparisonReviewSchema,
    x_operator: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    comparison = db.query(SkuComparison).filter(SkuComparison.id == comparison_id).first()
    if comparison is None:
        raise HTTPException(status_code=404, detail="SKU comparison not found")

    comparison.match_type = "MANUAL"
    comparison.status = 1 if payload.approved else -1
    _audit(
        db,
        action="COMPARISON_REVIEW",
        operator=_normalize_operator(x_operator),
        message=f"{'确认' if payload.approved else '驳回'}同款映射 #{comparison.id}",
    )
    db.commit()
    db.refresh(comparison)
    return ok(
        {
            "approved": payload.approved,
            "comparison_id": comparison.id,
            "status": comparison.status,
        },
        message="竞品匹配核验结果已更新",
    )


def _serialize_sku_basic(product: SkuProduct) -> SkuProductListItemSchema:
    return SkuProductListItemSchema(
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
        tags=[]
    )


def _seed_demo_categories(db: Session, platform: str):
    # Sample JD Category Tree
    # 1. 手机通讯
    c1 = CategoryNode(platform=platform, name="手机通讯", level=1, sort_order=1)
    db.add(c1); db.flush()
    c1_1 = CategoryNode(platform=platform, name="手机", level=2, parent_id=c1.id, sort_order=1)
    db.add(c1_1); db.flush()
    db.add_all([
        CategoryNode(platform=platform, name="智能手机", level=3, parent_id=c1_1.id, sort_order=1, external_id="653"),
        CategoryNode(platform=platform, name="老人机", level=3, parent_id=c1_1.id, sort_order=2, external_id="655"),
        CategoryNode(platform=platform, name="游戏手机", level=3, parent_id=c1_1.id, sort_order=3, external_id="12533")
    ])
    
    # 2. 电脑办公
    c2 = CategoryNode(platform=platform, name="电脑办公", level=1, sort_order=2)
    db.add(c2); db.flush()
    c2_1 = CategoryNode(platform=platform, name="电脑整机", level=2, parent_id=c2.id, sort_order=1)
    db.add(c2_1); db.flush()
    db.add_all([
        CategoryNode(platform=platform, name="游戏本", level=3, parent_id=c2_1.id, sort_order=1, external_id="672"),
        CategoryNode(platform=platform, name="轻薄本", level=3, parent_id=c2_1.id, sort_order=2, external_id="673"),
        CategoryNode(platform=platform, name="台式机", level=3, parent_id=c2_1.id, sort_order=3, external_id="675")
    ])
    
    # 3. 家用电器
    c3 = CategoryNode(platform=platform, name="家用电器", level=1, sort_order=3)
    db.add(c3); db.flush()
    c3_1 = CategoryNode(platform=platform, name="大家电", level=2, parent_id=c3.id, sort_order=1)
    db.add(c3_1); db.flush()
    db.add_all([
        CategoryNode(platform=platform, name="平板电视", level=3, parent_id=c3_1.id, sort_order=1, external_id="737"),
        CategoryNode(platform=platform, name="空调", level=3, parent_id=c3_1.id, sort_order=2, external_id="870"),
        CategoryNode(platform=platform, name="冰箱", level=3, parent_id=c3_1.id, sort_order=3, external_id="878")
    ])

    # 4. 美妆护肤
    c4 = CategoryNode(platform=platform, name="美妆护肤", level=1, sort_order=4)
    db.add(c4); db.flush()
    c4_1 = CategoryNode(platform=platform, name="面部护肤", level=2, parent_id=c4.id, sort_order=1)
    db.add(c4_1); db.flush()
    db.add_all([
        CategoryNode(platform=platform, name="补水保湿", level=3, parent_id=c4_1.id, sort_order=1, external_id="1316"),
        CategoryNode(platform=platform, name="洁面", level=3, parent_id=c4_1.id, sort_order=2, external_id="1317"),
        CategoryNode(platform=platform, name="精华", level=3, parent_id=c4_1.id, sort_order=3, external_id="1319")
    ])
    
    # Seed some mapping rules
    db.add_all([
        MappingRule(pattern="iPhone 15 Pro Max", unified_label="iPhone 15 PM", priority=10),
        MappingRule(pattern="iPhone 15 Pro", unified_label="iPhone 15 Pro", priority=9),
        MappingRule(pattern="拯救者 Y9000P", unified_label="Legion Y9000P", priority=5),
        MappingRule(pattern="MacBook Air", unified_label="MBA", priority=5),
        MappingRule(pattern="SK-II 神仙水", unified_label="SK-II Facial Treatment Essence", priority=10),
    ])
    
    db.commit()

    # Seed some cross-platform demo data if missing
    if db.query(SkuProduct).filter(SkuProduct.platform != "jd").count() == 0:
        _seed_cross_platform_demo(db)


def _seed_cross_platform_demo(db: Session):
    # Add some Tmall and Pinduoduo products that match JD ones
    # 1. iPhone 15 Pro Max
    db.add_all([
        SkuProduct(
            platform="tmall",
            sku_id="TM_778899",
            product_name="Apple/苹果 iPhone 15 Pro Max 5G 智能手机",
            normalized_name="iPhone 15 PM",
            brand_name="Apple",
            min_price=899900,
            max_price=999900,
            avg_price=949900,
            snapshot_count=5,
            status=1,
            category_level_1="手机通讯",
            category_level_3="智能手机",
        ),
        SkuProduct(
            platform="pinduoduo",
            sku_id="PDD_112233",
            product_name="【百亿补贴】Apple iPhone 15 Pro Max 256G 黑色",
            normalized_name="iPhone 15 PM",
            brand_name="Apple",
            min_price=859900,
            max_price=959900,
            avg_price=909900,
            snapshot_count=3,
            status=1,
            category_level_1="手机通讯",
            category_level_3="智能手机",
        ),
        SkuProduct(
            platform="tmall",
            sku_id="TM_445566",
            product_name="Lenovo/联想 拯救者 Y9000P 2024款 游戏本",
            normalized_name="Legion Y9000P",
            brand_name="Lenovo",
            min_price=999900,
            max_price=1099900,
            avg_price=1049900,
            snapshot_count=2,
            status=1,
            category_level_1="电脑办公",
            category_level_3="游戏本",
        ),
    ])
    db.flush()
    
    # Add some snapshots for these products
    from datetime import datetime, timedelta
    now = datetime.now()
    
    # Find the products we just added (they will be the latest ones)
    new_products = db.query(SkuProduct).filter(SkuProduct.platform.in_(["tmall", "pinduoduo"])).all()
    for p in new_products:
        if db.query(SkuPriceSnapshot).filter(SkuPriceSnapshot.sku_product_id == p.id).count() == 0:
            db.add(SkuPriceSnapshot(
                sku_product_id=p.id,
                captured_at=now - timedelta(hours=1),
                list_price=p.max_price or 999900,
                final_price=p.min_price or 899900,
                promo_text="Demo Snapshot"
            ))
    db.commit()
