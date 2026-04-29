import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.alert_repository import AlertRepository
from app.repositories.product_repository import ProductRepository
from app.models.product import PriceAlert, ProductSKU
from app.services.promotion_service import PromotionService


logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self):
        self.repo = AlertRepository()
        self.product_repo = ProductRepository()
        self.promo_service = PromotionService()

    def list_alerts(self, db: Session, user_id: int) -> list[PriceAlert]:
        alerts = self.repo.list_alerts(db, user_id)
        for alert in alerts:
            if alert.sku:
                promo = self.promo_service.calculate_final_price(alert.sku)
                alert.current_price = promo["final_price"]
            
            # Populate trigger_reason for response
            if alert.status == "triggered":
                alert.trigger_reason = f"低价捕获：已低于目标价 ¥{alert.target_price}"
            elif alert.status == "monitoring":
                if hasattr(alert, "current_price") and alert.current_price and alert.target_price:
                    diff_pct = (float(alert.current_price) - float(alert.target_price)) / float(alert.current_price)
                    if 0 < diff_pct <= 0.05:
                        alert.trigger_reason = "即将触发：距离目标价已不足 5%"
        return alerts


    def create_alert(self, db: Session, alert_in: dict) -> PriceAlert:
        # 1. Validate SKU existence
        sku = self.product_repo.get_sku_by_id(db, alert_in["sku_id"])
        if not sku:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"SKU ID {alert_in['sku_id']} not found")
        
        # 2. Check for duplicate active subscriptions for the same user + SKU
        existing = self.repo.get_alert_by_user_and_sku(db, alert_in["user_id"], alert_in["sku_id"])
        
        if existing:
            # Update existing alert instead of failing
            logger.info(f"Targeting existing alert ID {existing.id} for update (User {alert_in['user_id']}, SKU {alert_in['sku_id']})")
            existing.target_price = alert_in["target_price"]
            existing.notify_methods = alert_in.get("notify_methods", existing.notify_methods)
            existing.email = alert_in.get("email", existing.email)
            existing.phone = alert_in.get("phone", existing.phone)
            existing.status = "monitoring" # Reactivate in monitoring state
            db.commit()
            db.refresh(existing)
            return existing

        # Default status for new alerts
        alert_in.setdefault("status", "monitoring")
        alert_in.setdefault("is_triggered", False)
        alert = self.repo.create_alert(db, alert_in)
        logger.info(f"Created price alert ID {alert.id} for SKU {alert.sku_id} (Target: {alert.target_price})")
        return alert

    def delete_alert(self, db: Session, alert_id: int, user_id: int) -> bool:
        success = self.repo.delete_alert(db, alert_id, user_id)
        if success:
            logger.info(f"Deleted price alert ID {alert_id} for user {user_id}")
        return success

    def check_alerts(self, db: Session) -> list[PriceAlert]:
        """
        Scan all active (non-triggered) alerts and check if current final price <= target price.
        Returns a list of triggered alerts.
        """
        # Consistency Guard: Do not scan if a price update is currently in progress
        from app.models.task import CrawlTask
        active_update = (
            db.query(CrawlTask)
            .filter(CrawlTask.task_type == "price_update", CrawlTask.status == "running")
            .first()
        )
        if active_update:
            logger.info(f"Skipping alert scan: Price update (Job ID: {active_update.id}) is in progress.")
            return []

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
                alert.triggered_at = datetime.now()
                alert.triggered_price = current_final_price
                db.commit()
                triggered_alerts.append(alert)
                logger.info(f"ALERT TRIGGERED: ID {alert.id}, SKU {sku.id}, Price {current_final_price} <= Target {alert.target_price}")
        
        if triggered_alerts:
            logger.info(f"Total triggered alerts in this scan: {len(triggered_alerts)}")
        
        return triggered_alerts
