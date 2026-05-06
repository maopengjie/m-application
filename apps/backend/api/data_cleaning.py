import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from core.task_queue import enqueue_task
from db.session import get_db
from models import EtlLog, AnomalyAlert, CrawlEfficiency, ScrapeTaskRun, SkuProduct, SkuPriceSnapshot
from schemas.sku import ApiResponse
from services.price_statistics import apply_anomaly_verification_to_snapshots
from services.task_runs import mark_stale_scrape_runs
from pydantic import BaseModel

router = APIRouter(prefix="/data-cleaning", tags=["Data Cleaning"])

def dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(mode='json')
    if hasattr(model, "dict"):
        return model.dict()
    return model

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


class EtlLogSchema(BaseModel):
    id: int
    event_type: str
    platform: Optional[str]
    product_id: Optional[int]
    sku_id: Optional[str]
    field_name: Optional[str]
    original_value: Optional[str]
    cleaned_value: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AnomalyAlertSchema(BaseModel):
    id: int
    alert_type: str
    platform: str
    sku_id: str
    product_id: int | None = None
    alert_value: str
    threshold: Optional[str]
    is_verified: int
    verification_result: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class EfficiencySchema(BaseModel):
    id: int
    platform: str
    target_api: str
    response_time_ms: int
    status_code: int
    captured_at: datetime

    class Config:
        from_attributes = True


class AnomalyVerificationUpdateSchema(BaseModel):
    is_verified: int = 1
    verification_result: str | None = None


class RelatedScrapeRunSchema(BaseModel):
    id: int
    task_name: str
    status: str
    success_count: int
    failure_count: int
    summary_message: str | None = None
    created_at: datetime
    finished_at: datetime | None = None


class AnomalyContextSchema(BaseModel):
    anomaly_id: int
    product_id: int | None = None
    product_name: str | None = None
    product_url: str | None = None
    recent_runs: list[RelatedScrapeRunSchema]


class NotificationItemSchema(BaseModel):
    id: str
    date: str
    is_read: bool = False
    link: str
    message: str
    query: dict[str, str] | None = None
    title: str
    type: str


def _resolve_anomaly_product(db: Session, anomaly: AnomalyAlert) -> SkuProduct | None:
    if anomaly.product_id is not None:
        product = db.query(SkuProduct).filter(SkuProduct.id == anomaly.product_id).first()
        if product is not None:
            return product

    if anomaly.sku_id:
        return (
            db.query(SkuProduct)
            .filter(
                SkuProduct.platform == anomaly.platform,
                SkuProduct.sku_id == anomaly.sku_id,
            )
            .first()
        )
    return None


def _resolve_anomaly_scrape_url(db: Session, anomaly: AnomalyAlert) -> str | None:
    product = _resolve_anomaly_product(db, anomaly)
    if product and product.product_url:
        return product.product_url
    if anomaly.alert_value and anomaly.alert_value.startswith(("http://", "https://")):
        return anomaly.alert_value
    return None

@router.get("/logs")
def get_etl_logs(
    event_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(EtlLog)
    if event_type:
        query = query.filter(EtlLog.event_type == event_type)
    logs = query.order_by(EtlLog.created_at.desc()).limit(limit).all()
    return ok([dump_model(EtlLogSchema.model_validate(log)) for log in logs])


@router.get("/audit-logs")
def get_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = (
        db.query(EtlLog)
        .filter(EtlLog.event_type == "AUDIT")
        .order_by(EtlLog.created_at.desc(), EtlLog.id.desc())
        .limit(min(max(limit, 1), 100))
        .all()
    )
    return ok([dump_model(EtlLogSchema.model_validate(log)) for log in logs])

@router.get("/anomalies")
def get_anomalies(
    is_verified: Optional[int] = None,
    alert_type: Optional[str] = None,
    platform: Optional[str] = None,
    sku_id: Optional[str] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(AnomalyAlert)
    if is_verified is not None:
        query = query.filter(AnomalyAlert.is_verified == is_verified)
    if alert_type:
        query = query.filter(AnomalyAlert.alert_type == alert_type)
    if platform:
        query = query.filter(AnomalyAlert.platform == platform)
    if sku_id:
        query = query.filter(AnomalyAlert.sku_id.ilike(f"%{sku_id.strip()}%"))
    if start_at is not None:
        query = query.filter(AnomalyAlert.created_at >= start_at)
    if end_at is not None:
        query = query.filter(AnomalyAlert.created_at <= end_at)
    anomalies = query.order_by(AnomalyAlert.created_at.desc()).limit(limit).all()
    return ok([dump_model(AnomalyAlertSchema.model_validate(a)) for a in anomalies])


@router.get("/anomalies/{anomaly_id}/context")
def get_anomaly_context(anomaly_id: int, db: Session = Depends(get_db)):
    anomaly = db.query(AnomalyAlert).filter(AnomalyAlert.id == anomaly_id).first()
    if anomaly is None:
        raise HTTPException(status_code=404, detail="Anomaly alert not found")

    product = _resolve_anomaly_product(db, anomaly)

    run_query = db.query(ScrapeTaskRun)
    run_filters = []
    if product and product.product_url:
        run_filters.append(ScrapeTaskRun.requested_url == product.product_url)
        run_filters.append(ScrapeTaskRun.failed_items_json.ilike(f"%{product.product_url}%"))
    if product:
        run_filters.append(ScrapeTaskRun.failed_items_json.ilike(f'%\"product_id\": {product.id}%'))
        run_filters.append(ScrapeTaskRun.failed_items_json.ilike(f'%\"product_id\":{product.id}%'))
    if anomaly.alert_value:
        run_filters.append(ScrapeTaskRun.requested_url == anomaly.alert_value)
        run_filters.append(ScrapeTaskRun.failed_items_json.ilike(f"%{anomaly.alert_value}%"))

    recent_runs = []
    if run_filters:
        recent_runs = (
            run_query.filter(or_(*run_filters))
            .order_by(ScrapeTaskRun.created_at.desc(), ScrapeTaskRun.id.desc())
            .limit(5)
            .all()
        )

    payload = AnomalyContextSchema(
        anomaly_id=anomaly.id,
        product_id=product.id if product else anomaly.product_id,
        product_name=product.normalized_name or product.product_name if product else None,
        product_url=product.product_url if product else None,
        recent_runs=[
            RelatedScrapeRunSchema(
                id=run.id,
                task_name=run.task_name,
                status=run.status,
                success_count=run.success_count,
                failure_count=run.failure_count,
                summary_message=run.summary_message,
                created_at=run.created_at,
                finished_at=run.finished_at,
            )
            for run in recent_runs
        ],
    )
    return ok(dump_model(payload))


@router.post("/anomalies/{anomaly_id}/retry-scrape")
def retry_anomaly_scrape(
    anomaly_id: int,
    x_operator: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    anomaly = db.query(AnomalyAlert).filter(AnomalyAlert.id == anomaly_id).first()
    if anomaly is None:
        raise HTTPException(status_code=404, detail="Anomaly alert not found")
    if anomaly.alert_type not in {"SCRAPE_FAILURE", "DATA_MISSING"}:
        raise HTTPException(status_code=400, detail="Only scrape/data anomalies can be retried")

    scrape_url = _resolve_anomaly_scrape_url(db, anomaly)
    if not scrape_url:
        raise HTTPException(status_code=400, detail="No product URL available for retry")

    run = ScrapeTaskRun(
        task_name="scrape_product",
        trigger_source="ANOMALY_RETRY",
        platform=anomaly.platform,
        requested_url=scrape_url,
        status="PENDING",
        summary_message=f"异常 #{anomaly.id} 触发重抓",
    )
    db.add(run)
    db.flush()

    try:
        task_id = enqueue_task("tasks.scraping.scrape_product", scrape_url, run.id)
        run.task_id = task_id
        _audit(
            db,
            action="ANOMALY_RETRY",
            operator=_normalize_operator(x_operator),
            product_id=anomaly.product_id,
            sku_id=anomaly.sku_id,
            message=f"异常 #{anomaly.id} 触发重抓 run #{run.id}",
        )
        db.commit()
        db.refresh(run)
    except Exception as exc:
        run.status = "FAILED"
        run.summary_message = "异常重抓任务投递失败"
        run.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=503, detail="Scrape worker is unavailable") from exc

    return ok(
        {
            "anomaly_id": anomaly.id,
            "run_id": run.id,
            "task_id": run.task_id,
            "url": scrape_url,
        },
        message="异常重抓任务已投递",
    )


@router.get("/anomalies/export")
def export_anomalies(
    is_verified: Optional[int] = None,
    alert_type: Optional[str] = None,
    platform: Optional[str] = None,
    sku_id: Optional[str] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    query = db.query(AnomalyAlert)
    if is_verified is not None:
        query = query.filter(AnomalyAlert.is_verified == is_verified)
    if alert_type:
        query = query.filter(AnomalyAlert.alert_type == alert_type)
    if platform:
        query = query.filter(AnomalyAlert.platform == platform)
    if sku_id:
        query = query.filter(AnomalyAlert.sku_id.ilike(f"%{sku_id.strip()}%"))
    if start_at is not None:
        query = query.filter(AnomalyAlert.created_at >= start_at)
    if end_at is not None:
        query = query.filter(AnomalyAlert.created_at <= end_at)

    anomalies = query.order_by(AnomalyAlert.created_at.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "alert_type",
            "platform",
            "sku_id",
            "alert_value",
            "threshold",
            "is_verified",
            "verification_result",
            "message",
            "created_at",
        ]
    )
    for item in anomalies:
        writer.writerow(
            [
                item.id,
                item.alert_type,
                item.platform,
                item.sku_id,
                item.alert_value,
                item.threshold or "",
                item.is_verified,
                item.verification_result or "",
                item.message or "",
                item.created_at.isoformat(sep=" ", timespec="seconds"),
            ]
        )

    filename = f"anomaly-alerts-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/efficiency")
def get_efficiency(
    platform: str = "jd",
    limit: int = 100,
    db: Session = Depends(get_db)
):
    records = db.query(CrawlEfficiency).filter(CrawlEfficiency.platform == platform).order_by(CrawlEfficiency.captured_at.desc()).limit(limit).all()
    return ok([dump_model(EfficiencySchema.model_validate(r)) for r in records])

@router.get("/stats")
def get_cleaning_stats(db: Session = Depends(get_db)):
    cleaning_count = db.query(func.count(EtlLog.id)).filter(EtlLog.event_type == "CLEANING").scalar() or 0
    anomaly_count = db.query(func.count(AnomalyAlert.id)).scalar() or 0
    avg_response = db.query(func.avg(CrawlEfficiency.response_time_ms)).scalar() or 0
    total_efficiency = db.query(func.count(CrawlEfficiency.id)).scalar() or 0
    success_efficiency = (
        db.query(func.count(CrawlEfficiency.id))
        .filter(CrawlEfficiency.status_code >= 200, CrawlEfficiency.status_code < 400)
        .scalar()
        or 0
    )
    success_rate = round((success_efficiency * 100 / total_efficiency), 1) if total_efficiency else 0

    return ok({
        "total_cleaned": cleaning_count,
        "total_anomalies": anomaly_count,
        "avg_response_time": round(float(avg_response), 2),
        "success_rate": success_rate,
    })


@router.get("/notifications")
def get_data_center_notifications(limit: int = 10, db: Session = Depends(get_db)):
    if mark_stale_scrape_runs(db):
        db.commit()

    safe_limit = min(max(limit, 1), 30)
    anomalies = (
        db.query(AnomalyAlert)
        .filter(AnomalyAlert.is_verified == 0)
        .order_by(AnomalyAlert.created_at.desc(), AnomalyAlert.id.desc())
        .limit(safe_limit)
        .all()
    )
    runs = (
        db.query(ScrapeTaskRun)
        .filter(ScrapeTaskRun.status.in_(["FAILED", "PARTIAL_SUCCESS", "TIMEOUT", "SUCCESS"]))
        .order_by(ScrapeTaskRun.created_at.desc(), ScrapeTaskRun.id.desc())
        .limit(safe_limit)
        .all()
    )
    lows = (
        db.query(SkuPriceSnapshot, SkuProduct)
        .join(SkuProduct, SkuProduct.id == SkuPriceSnapshot.sku_product_id)
        .filter(
            SkuPriceSnapshot.is_anomalous == 0,
            SkuPriceSnapshot.captured_at >= datetime.now() - timedelta(hours=24),
            SkuProduct.min_price == SkuPriceSnapshot.final_price,
        )
        .order_by(SkuPriceSnapshot.captured_at.desc())
        .limit(safe_limit)
        .all()
    )

    items: list[NotificationItemSchema] = []
    for anomaly in anomalies:
        items.append(
            NotificationItemSchema(
                id=f"anomaly-{anomaly.id}",
                date=anomaly.created_at.isoformat(sep=" ", timespec="seconds"),
                link="/data-center/data-cleaning",
                message=anomaly.message or anomaly.alert_value,
                query={"tab": "anomalies", "status": "pending"},
                title=f"待核验异常：{anomaly.sku_id}",
                type=anomaly.alert_type,
            )
        )
    for run in runs:
        is_success = run.status == "SUCCESS"
        items.append(
            NotificationItemSchema(
                id=f"run-{run.id}",
                date=run.created_at.isoformat(sep=" ", timespec="seconds"),
                link="/data-center/sku-repository",
                message=run.summary_message or run.error_message or ("采集任务已完成" if is_success else "采集任务需要处理"),
                query={
                    "runId": str(run.id),
                    "taskStatus": "open" if is_success else "problem",
                },
                title=f"{'任务完成' if is_success else '抓取失败'}：#{run.id}",
                type="SCRAPE_RUN",
            )
        )
    for snapshot, product in lows:
        items.append(
            NotificationItemSchema(
                id=f"low-{snapshot.id}",
                date=snapshot.captured_at.isoformat(sep=" ", timespec="seconds"),
                link="/data-center/price-time-series",
                message=f"{product.normalized_name or product.product_name} 命中历史低价",
                query={"recent": "24h", "sku": product.sku_id},
                title=f"历史低价：{product.sku_id}",
                type="PRICE_LOW",
            )
        )

    items.sort(key=lambda item: item.date, reverse=True)
    return ok([dump_model(item) for item in items[:safe_limit]])


@router.put("/anomalies/{anomaly_id}")
def verify_anomaly(
    anomaly_id: int,
    payload: AnomalyVerificationUpdateSchema,
    x_operator: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    anomaly = db.query(AnomalyAlert).filter(AnomalyAlert.id == anomaly_id).first()
    if anomaly is None:
        raise HTTPException(status_code=404, detail="Anomaly alert not found")

    anomaly.is_verified = 1 if payload.is_verified else 0
    anomaly.verification_result = payload.verification_result
    recompute_result = apply_anomaly_verification_to_snapshots(
        db,
        anomaly,
        payload.verification_result,
    )
    _audit(
        db,
        action="ANOMALY_VERIFY",
        operator=_normalize_operator(x_operator),
        product_id=anomaly.product_id,
        sku_id=anomaly.sku_id,
        message=f"核验异常 #{anomaly.id}：{payload.verification_result or '已核验'}",
    )
    db.commit()
    db.refresh(anomaly)
    return ok(
        {
            "anomaly": dump_model(AnomalyAlertSchema.model_validate(anomaly)),
            "price_recompute": recompute_result,
        },
        message="核验结果已更新，价格统计已重算",
    )
