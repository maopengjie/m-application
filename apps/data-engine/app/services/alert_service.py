from sqlalchemy.orm import Session
from app.repositories.alert_repository import AlertRepository
from app.models.product import PriceAlert


class AlertService:
    def __init__(self):
        self.repo = AlertRepository()

    def list_alerts(self, db: Session, user_id: int) -> list[dict]:
        alerts = self.repo.list_alerts(db, user_id)
        results = []
        for alert in alerts:
            # Map attributes to match PriceAlertResponse schema
            alert_dict = {
                "id": alert.id,
                "sku_id": alert.sku_id,
                "target_price": alert.target_price,
                "user_id": alert.user_id,
                "created_at": alert.created_at,
                "product_title": alert.sku.title if alert.sku else "Unknown",
                "product_image": alert.sku.product.main_image if alert.sku and alert.sku.product else None,
                "current_price": alert.sku.price if alert.sku else 0,
                "notify_methods": ["web"]  # Default for MVP
            }
            results.append(alert_dict)
        return results

    def create_alert(self, db: Session, alert_in: dict) -> PriceAlert:
        return self.repo.create_alert(db, alert_in)

    def delete_alert(self, db: Session, alert_id: int) -> bool:
        return self.repo.delete_alert(db, alert_id)
