from app.core.database import SessionLocal
from app.services.collector_service import CollectorService

collector_service = CollectorService()


def refresh_prices_job():
    """Scheduled job to update all product prices."""
    with SessionLocal() as db:
        collector_service.run_collection(db)


def register_price_jobs(scheduler) -> None:
    scheduler.add_job(
        refresh_prices_job,
        "interval",
        minutes=5, # Update every 10 minutes for Phase 8 testing
        id="price-refresh-skus",
        replace_existing=True,
    )
