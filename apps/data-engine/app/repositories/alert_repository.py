from sqlalchemy.orm import Session, joinedload
from app.models.product import PriceAlert, ProductSKU


class AlertRepository:
    def list_alerts(self, db: Session, user_id: int) -> list[PriceAlert]:
        return (
            db.query(PriceAlert)
            .options(joinedload(PriceAlert.sku).joinedload(ProductSKU.product))
            .filter(PriceAlert.user_id == user_id)
            .order_by(PriceAlert.created_at.desc())
            .all()
        )

    def create_alert(self, db: Session, alert_data: dict) -> PriceAlert:
        db_alert = PriceAlert(**alert_data)
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        return db_alert

    def delete_alert(self, db: Session, alert_id: int) -> bool:
        db_alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
        if db_alert:
            db.delete(db_alert)
            db.commit()
            return True
        return False
