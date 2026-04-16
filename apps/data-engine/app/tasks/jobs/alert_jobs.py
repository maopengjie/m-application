from app.core.database import SessionLocal
from app.services.alert_service import AlertService

def run_price_scanning():
    """Background job to scan prices and trigger alerts."""
    db = SessionLocal()
    try:
        service = AlertService()
        triggered = service.check_alerts(db)
        if triggered:
            print(f"Background check: {len(triggered)} alerts triggered.")
    finally:
        db.close()

def register_alert_jobs(scheduler) -> None:
    scheduler.add_job(
        run_price_scanning,
        "interval",
        minutes=1, # Check every minute for MVP
        id="alert-price-scan",
        replace_existing=True,
    )
