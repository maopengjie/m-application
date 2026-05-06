from __future__ import annotations

from sqlalchemy.orm import Session

from models import AnomalyAlert


def resolve_recovered_data_anomalies(
    db: Session,
    *,
    platform: str,
    product_id: int | None = None,
    product_url: str | None = None,
    sku_id: str,
) -> int:
    query = db.query(AnomalyAlert).filter(
        AnomalyAlert.alert_type.in_(["SCRAPE_FAILURE", "DATA_MISSING"]),
        AnomalyAlert.platform == platform,
        AnomalyAlert.sku_id == sku_id,
        AnomalyAlert.is_verified == 0,
    )
    if product_id is not None and product_url:
        query = query.filter(
            (AnomalyAlert.product_id == product_id)
            | (AnomalyAlert.alert_value == product_url)
        )
    elif product_id is not None:
        query = query.filter(AnomalyAlert.product_id == product_id)
    elif product_url:
        query = query.filter(AnomalyAlert.alert_value == product_url)

    recovered = query.all()
    for anomaly in recovered:
        anomaly.is_verified = 1
        anomaly.verification_result = "重抓成功，系统自动关闭异常"
        anomaly.message = f"{anomaly.message or ''}；重抓已恢复".strip("；")

    if recovered:
        db.flush()
    return len(recovered)
