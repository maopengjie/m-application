from sqlalchemy.orm import Session
from app.repositories.alert_repository import AlertRepository
from app.models.product import PriceAlert


class AlertService:
    def __init__(self):
        self.repo = AlertRepository()

    def list_alerts(self, db: Session, user_id: int) -> list[PriceAlert]:
        return self.repo.list_alerts(db, user_id)

    def create_alert(self, db: Session, alert_in: dict) -> PriceAlert:
        return self.repo.create_alert(db, alert_in)
