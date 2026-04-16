from sqlalchemy.orm import Session
from app.repositories.alert_repository import AlertRepository
from app.models.product import PriceAlert, ProductSKU
from app.services.promotion_service import PromotionService


class AlertService:
    def __init__(self):
        self.repo = AlertRepository()
        self.promo_service = PromotionService()

    def list_alerts(self, db: Session, user_id: int) -> list[PriceAlert]:
        return self.repo.list_alerts(db, user_id)

    def create_alert(self, db: Session, alert_in: dict) -> PriceAlert:
        # Default status for new alerts
        alert_in.setdefault("status", "active")
        alert_in.setdefault("is_triggered", False)
        return self.repo.create_alert(db, alert_in)

    def delete_alert(self, db: Session, alert_id: int) -> bool:
        return self.repo.delete_alert(db, alert_id)

    def check_alerts(self, db: Session) -> list[PriceAlert]:
        """
        Scan all active (non-triggered) alerts and check if current final price <= target price.
        Returns a list of triggered alerts.
        """
        active_alerts = self.repo.get_active_alerts(db)
        triggered_alerts = []

        for alert in active_alerts:
            sku = alert.sku
            if not sku:
                continue
            
            # Calculate current final price
            promo = self.promo_service.calculate_final_price(sku)
            current_final_price = promo["final_price"]

            if current_final_price <= alert.target_price:
                # Triggered!
                alert.is_triggered = True
                alert.status = "triggered"
                db.commit()
                triggered_alerts.append(alert)
        
        return triggered_alerts
