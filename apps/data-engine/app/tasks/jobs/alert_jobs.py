import logging
from app.core.database import SessionLocal
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


def run_price_scanning():
    """Background job to scan prices and trigger alerts."""
    logger.info("Alert scan job started.")
    db = SessionLocal()
    try:
        service = AlertService()
        triggered = service.check_alerts(db)
        if triggered:
            logger.info(f"Alert scan completed: {len(triggered)} alerts triggered.")
        else:
            logger.info("Alert scan completed: No alerts triggered.")
    except Exception as e:
        logger.error(f"Alert scan job failed with error: {e}", exc_info=True)
    finally:
        db.close()

def register_alert_jobs(scheduler) -> None:
    scheduler.add_job(
        run_price_scanning,
        "interval",
        minutes=1, # Check every minute for MVP
        id="alert-price-scan",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=30,
    )
