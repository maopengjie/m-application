from app.core.database import SessionLocal
from app.services.price_service import PriceMonitorService

price_monitor_service = PriceMonitorService()


def refresh_prices_job():
    with SessionLocal() as db:
        price_monitor_service.update_all_prices(db)


def register_price_jobs(scheduler) -> None:
    scheduler.add_job(
        refresh_prices_job,
        "interval",
        minutes=15,
        id="price-refresh",
        replace_existing=True,
    )
