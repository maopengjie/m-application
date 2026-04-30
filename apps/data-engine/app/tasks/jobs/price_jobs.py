from app.core.database import SessionLocal
from app.services.collector_service import CollectorService

collector_service = CollectorService()


import logging

logger = logging.getLogger(__name__)


def refresh_prices_job():
    """Scheduled job to update all product prices."""
    logger.info("Price refresh job started.")
    try:
        with SessionLocal() as db:
            collector_service.run_collection(db)
        logger.info("Price refresh job completed successfully.")
    except Exception as e:
        logger.error(f"Price refresh job failed: {e}", exc_info=True)


def register_price_jobs(scheduler) -> None:
    scheduler.add_job(
        refresh_prices_job,
        "interval",
        minutes=5, # Update every 10 minutes for Phase 8 testing
        id="price-refresh-skus",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
