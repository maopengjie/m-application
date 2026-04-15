from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price_monitor import PriceMonitor


class PriceMonitorRepository:
    def list(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[PriceMonitor]:
        stmt = select(PriceMonitor).offset(skip).limit(limit).order_by(PriceMonitor.id.desc())
        return db.scalars(stmt).all()

    def get(self, db: Session, monitor_id: int) -> PriceMonitor | None:
        return db.get(PriceMonitor, monitor_id)

    def create(self, db: Session, payload: dict) -> PriceMonitor:
        monitor = PriceMonitor(**payload)
        db.add(monitor)
        db.commit()
        db.refresh(monitor)
        return monitor

    def save(self, db: Session, monitor: PriceMonitor) -> PriceMonitor:
        db.add(monitor)
        db.commit()
        db.refresh(monitor)
        return monitor
